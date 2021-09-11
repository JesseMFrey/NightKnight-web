import io
import serial
import re

#custom exception for commands
class CommandError(Exception):
    pass

class NKSetting:
    def __init__(self, name, get_func, set_func):
        self.name = name
        self.get_func = get_func
        self.set_func = set_func

        self.value = None

    def add(self, dest):
        dest[self.name] = self

    def clear(self):
        self.value = None

    def get(self, **kwargs):
        #get force argument
        force = kwargs.pop('force',False)

        #check if we have a value
        if force or self.value is None:
            #run get function
            self.get_func(**kwargs)
        return self.value
    def __repr__(self):
        return f'{self.__class__.__name__}<name={repr(self.name)}, value = {repr(self.value)}>'

    def set(self, *args, **kwargs):
        if self.set_func is None:
            raise RuntimeError(f'{self.name} can not be set')

        #get force argument
        force = kwargs.pop('force',False)

        #check if we only have one input value
        single_val= len(args)==1 and not kwargs

        if force or not single_val or self.value != args[0]:
            self.set_func(*args, **kwargs)

            if single_val:
                self.value = args[0]
            else:
                self.clear()

class NKMetta:
    def __init__(self, name, set_func):
        self.name = name
        self.set_func = set_func

    def add(self, dest):
        dest[self.name] = self

    def set(self, *args, **kwargs):
        self.set_func(*args, **kwargs)

class NightKnight:

    NC_modes=("static", "fade", "flash", "blip","pattern")
    chute_modes=("static", "fade", "flash", "blip")
    saved_settings = ('pattern', 'value', 'brightness', 'color', 'color_list',
                      'flight_pattern', 'flight_altitude')

    def __init__(self,port,debug=False):
        self._sobj=serial.Serial(port,timeout=0.5) 
        self._textin=io.TextIOWrapper(io.BufferedReader(self._sobj))
        self.port_name=port
        self.debug=debug

        self.cache = {}

        #add lists first
        NKSetting('pattern_list',        self.get_patterns,        None).add(self.cache)
        NKSetting('flight_pattern_list', self.get_flight_patterns, None).add(self.cache)
        NKSetting('clist_list',          self.get_clists,          None).add(self.cache)

        #add everything else
        NKSetting('pattern',    self.get_pattern,  self.set_pattern).add(self.cache)
        NKSetting('value',      self.get_value,    self.set_value  ).add(self.cache)
        NKSetting('brightness', self.get_brightness,    self.set_brightness  ).add(self.cache)
        NKSetting('color',      self.get_color,    self.set_color  ).add(self.cache)
        NKSetting('color_list', self.get_clists,   self.set_clist  ).add(self.cache)

        #nosecone things
        NKSetting('NC_mode',   self.get_NC, None).add(self.cache)
        NKSetting('NC_val1',  self.get_NC, None).add(self.cache)
        NKSetting('NC_val2',  self.get_NC, None).add(self.cache)
        NKSetting('NC_t1', self.get_NC, None).add(self.cache)
        NKSetting('NC_t2', self.get_NC, None).add(self.cache)
        NKMetta('NC', self.set_NC).add(self.cache)

        #chute things
        NKSetting('chute_mode',   self.get_chute, None).add(self.cache)
        NKSetting('chute_val1',  self.get_chute, None).add(self.cache)
        NKSetting('chute_val2',  self.get_chute, None).add(self.cache)
        NKSetting('chute_t1', self.get_chute, None).add(self.cache)
        NKSetting('chute_t2', self.get_chute, None).add(self.cache)
        NKMetta('chute', self.set_chute).add(self.cache)

        #settings
        NKSetting('ram_set',   self.get_ram_settings,   None).add(self.cache)
        NKSetting('flash_set', self.get_flash_settings, None).add(self.cache)

        #flight pattern things
        NKSetting('flight_pattern',  self.get_flight_patterns, self.set_flight_pattern).add(self.cache)
        NKSetting('flight_altitude', self.get_altitude,        self.set_altitude      ).add(self.cache)

        #nightlight mode
        NKSetting('nightlight', self.get_nightlight, self.set_nightlight).add(self.cache)

    def get(self, key, **kwargs):

        return self.cache[key].get(**kwargs)

    def set(self, key, *args, **kwargs):

        self.cache[key].set(*args, **kwargs)

        #invalidate ram settings for some things
        if key in self.saved_settings:
            self._clear('ram_set')

    def get_keys(self):
        return tuple(self.cache.keys())

    def _set(self, key, value):
        self.cache[key].value = value

    def _clear(self, key):
        #check for metta settings
        val = self.cache[key]
        if isinstance(val, NKMetta):
            for k in self.get_keys():
                if k.startswith(key+'_'):
                    #clear value
                    self._clear(k)
        else:
            val.clear()

    def set_pattern(self,pat):
        self._command(f'pat {pat}')

        line=self.get_line()


        mstr=re.match('LED pattern set to \'(?P<pat>[^\']+)\'',line)
        if(mstr and mstr.group('pat')==pat):
            #success!
            return

        mnum=re.match('LED pattern set to \#(?P<pnum>[0-9]+)',line)
        if(mnum and mnum.group('pnum')==str(pat)):
            #success!
            return

        raise CommandError(f'Unable to parse response \'{line}\'')

    def get_patterns(self):
        self._command('pat')
        #get line
        line=self.get_line()
        if(line.rstrip() != 'Possible pattern names :'):
            raise CommandError(f'Unexpected output \'{line}\'')
        #get line before loop
        line=self.get_line()
        #empty array
        patterns=[]
        current=None
        while(not line.startswith('>')):
            #strip spaces
            pat=line.strip()
            #check if this is the current pattern
            if(pat.startswith('*')):
                #strip indicator
                pat=pat[1:]
                current=pat
            #add to list
            patterns.append(pat)
            #get next line
            line=self.get_line()
        #set patterns and current pattern
        self._set('pattern_list',tuple(patterns))
        self._set('pattern',current)

    def get_pattern(self):
        self._command('get pat')
        #get line
        line=self.get_line()
        #split line and strip whitespace
        name, pat = [s.strip() for s in line.split(':')]
        #check for error
        if name == 'Error':
            raise RuntimeError(f'problem with command \'{pat}\'')
        elif name == 'LED pattern':
            self._set('pattern', pat)
        else:
            raise RuntimeError(f'unexpected response to \'get\' command \'{line.strip()}\'')

    def set_flight_pattern(self,pat):
        self._command(f'fpat {pat}')

        line=self.get_line()

        if(not line.startswith('>')):
            raise CommandError(f'Unable to parse response \'{line}\'')

    def get_flight_patterns(self):
        self._command('fpat')
        #get line before loop
        line=self.get_line()
        #empty array
        patterns=[]
        current = None
        while(not line.startswith('>')):
            #strip spaces
            pat=line.strip()
            #check if this is the current pattern
            if(pat.startswith('>')):
                #strip indicator
                pat=pat[1:]
                current=pat
            #add to list
            patterns.append(pat)
            #get next line
            line=self.get_line()
        #set patterns and current pattern
        self._set('flight_pattern_list',tuple(patterns))
        self._set('flight_pattern',current)

    def set_value(self,value):
        self._command(f'value {value}')
        #get line
        line=self.get_line().strip()
        expected=f'Value : {value}'
        if(expected not in line):
            raise CommandError(f'expected \'{expected}\' but got \'{line}\'')

    def get_value(self):
        self._command(f'value')
        #get line
        line=self.get_line()
        m=re.match(f'Value : (?P<val>[0-9]+)',line)
        if(not m):
            raise CommandError(f'unable to parse \'{line}\'')
        #set value
        self._set('value', int(m.group('val')))

    def get_color(self):
        self._command('color')
        #get a line for color
        line=self.get_line()
        m=re.match(r'color : (?P<brt>0x[A-F0-9]+) (?P<red>0x[A-F0-9]+) (?P<green>0x[A-F0-9]+) (?P<blue>0x[A-F0-9]+)',line)
        if(not m):
            raise RuntimeError(f'unable to parse \'{line}\'')
        brt = int(m.group('brt'),16)
        red = int(m.group('red'),16)
        green = int(m.group('green'),16)
        blue = int(m.group('blue'),16)
        self._set('brightness', brt)
        self._set('color', (red, green, blue))

    def set_color(self,color):
        self._command(f'color {color[0]} {color[1]} {color[2]}')
        #get a line for color
        line=self.get_line()
        m=re.match(r'color : (?P<brt>0x[A-F0-9]+) (?P<red>0x[A-F0-9]+) (?P<green>0x[A-F0-9]+) (?P<blue>0x[A-F0-9]+)',line)
        if(not m):
            raise RuntimeError(f'unable to parse \'{line}\'')
        #TODO : check to see if color matches??

    def set_brightness(self,brt):
        self._command(f'brt {brt}')
        #get a line for brightness
        line=self.get_line()
        m=re.match(r'Brightness (?P<brt>[0-9]+)',line)
        if(not m):
            raise RuntimeError(f'unable to parse \'{line}\'')
        brt_val = m.group('brt')
        #get line, should be the prompt '>', otherwise error
        line=self.get_line()
        #check for '>' char
        if(not line.startswith('>')):
            raise RuntimeError(f'Could not set NC \'{line.strip()}\'')
        if int(brt_val) != int(brt):
            raise RuntimeError(f'Set brightness \'{brt_val}\' does not match \'{brt}\'')

    def get_brightness(self):
        self._command(f'brt')
        #get a line for brightness
        line=self.get_line()
        m=re.match(r'Brightness (?P<brt>[0-9]+)',line)
        if(not m):
            raise RuntimeError(f'unable to parse \'{line}\'')
        brt = int(m.group('brt'))
        #check for '>' char
        if(not line.startswith('>')):
            raise RuntimeError(f'Could not set NC \'{line.strip()}\'')
        self._set('brightness', brt)


    def get_clists(self):
        self._command('clist')
        #get line
        line=self.get_line()
        if(line.rstrip() != 'Color Lists:'):
            raise CommandError(f'Unexpected output \'{line}\'')
        #get line before loop
        line=self.get_line()
        #empty array
        lists=[]
        current=None
        while(not line.startswith('>')):
            #strip spaces
            lname=line.strip()
            #check if this is the current pattern
            if(lname.startswith('>')):
                #strip indicator
                lname=lname[1:]
                current=lname
            #add to list
            lists.append(lname)
            #get next line
            line=self.get_line()
        #set patterns and current pattern
        self._set('clist_list',tuple(lists))
        self._set('color_list',current)

    def set_clist(self,clist):
        self._command(f'clist {clist}')
        line=self.get_line()
        err_prefix='Error : '
        if(line.startswith(err_prefix)):
            raise RuntimeError(line[len(err_prefix):].strip())

    def get_NC(self):
        #status={}
        self._command('NC')
        line=self.get_line()
        #line for PWM status
        m=re.match(r'Nosecone PWM : 0X(?P<hex>[0-9A-F]{3}) = (?P<percent>\d+\.\d+)',line)
        if(not m):
            raise RuntimeError(f'unable to parse \'{line}\'')
        #status['percent']=float(m.group('percent'))
        #status['PWM']=int(m.group('hex'),16)
        #get line for heading
        line=self.get_line().strip()
        if(line != 'Nosecone:'):
            raise RuntimeError(f'unable to parse \'{line}\'')
        #get line for mode
        line=self.get_line()
        m=re.match(r'\s+Mode : (?P<mode>\S+)',line)
        if(not m):
            raise RuntimeError(f'unable to parse \'{line}\'')
        #status|=m.groupdict()
        mode = m.group('mode')
        self._set('NC_mode', mode)
        #if we are in pattern mode we'll get an extra line
        if(mode =='pattern'):
            line=self.get_line()
            m=re.match(r'\s+Pattern Mode : (?P<mode>\S+)',line)
            if(not m):
                raise RuntimeError(f'unable to parse \'{line}\'')
            #status|=m.groupdict()
            #self._set('NC_mode', m.group('mode'))

        for name in ('val1','val2','t1','t2','count','state','dir'):
            #get line
            line=self.get_line()
            m=re.match(r'\s+'+name+r' : (?P<val>[+-]?[0-9]+)',line)
            if(not m):
                raise RuntimeError(f'unable to parse \'{line}\' expected \'{name}\'')
            if name in ('val1','val2','t1','t2'):
                #set in cache
                self._set('NC_'+name, int(m.group('val')))


    def set_NC(self,mode,val1=0,val2=0,t1=0,t2=0):
        self._command(f'NC {mode} {val1} {val2} {t1} {t2}')
        #get line, should be the prompt '>', otherwise error
        line=self.get_line()
        #check for '>' char
        if(not line.startswith('>')):
            raise RuntimeError(f'Could not set NC \'{line.strip()}\'')
        #update cache values
        self._set('NC_mode',mode)
        self._set('NC_val1',val1)
        self._set('NC_val2',val2)
        self._set('NC_t1',t1)
        self._set('NC_t2',t2)

    def get_chute(self):
        self._command('chute')
        line=self.get_line()
        #line for PWM status
        m=re.match(r'Chute PWM\s+: 0X(?P<hex>[0-9A-F]{3}) = (?P<percent>\d+\.\d+)',line)
        if(not m):
            raise RuntimeError(f'unable to parse \'{line}\'')
        #status['percent']=float(m.group('percent'))
        #status['PWM']=int(m.group('hex'),16)
        #get line for heading
        line=self.get_line().strip()
        if(line != 'Chute:'):
            raise RuntimeError(f'unable to parse \'{line}\'')
        #get line for mode
        line=self.get_line()
        m=re.match(r'\s+Mode : (?P<mode>\S+)',line)
        if(not m):
            raise RuntimeError(f'unable to parse \'{line}\'')
        #status|=m.groupdict()
        self._set('chute_mode', m.group('mode'))

        for name in ('val1','val2','t1','t2','count','state','dir'):
            #get line
            line=self.get_line()
            m=re.match(r'\s+'+name+r' : (?P<val>[+-]?[0-9]+)',line)
            if(not m):
                raise RuntimeError(f'unable to parse \'{line}\' expected \'{name}\'')
            if name in ('val1','val2','t1','t2'):
                #set in cache
                self._set('chute_'+name, int(m.group('val')))


    def set_chute(self,mode,val1=0,val2=0,t1=0,t2=0):
        self._command(f'chute {mode} {val1} {val2} {t1} {t2}')
        #get line, should be the prompt '>', otherwise error
        line=self.get_line()
        #check for '>' char
        if(not line.startswith('>')):
            raise RuntimeError(f'Could not set chute \'{line.strip()}\'')

    def read_ADC(self):
        self._command('ADC')
        #get header line
        line=self.get_line()
        #check line
        if('ADC values' not in line):
            raise RuntimeError(f'Unexpected line \'{line}\'')
        #initialize dict
        dat={}
        #get line
        line=self.get_line()
        while(line and not line.startswith('>')):
            #strip spaces
            name,value=line.strip().split(':')
            print(f'Name : \'{name}\' Value : \'{value}\'')
            #TODO : make this a bit more robust
            val,unit=value.split()
            value=float(val)
            dat[name.strip()]=(value,unit)
            #get next line
            line=self.get_line()

        return dat

    def simulate(self):
        self._command('sim')
        #get line
        line=self.get_line()
        while(line and not line.startswith('>')):
            #TODO : stream this somehow?
            print(f'Sim : {line.strip()}')
            line=self.get_line()

    def _get_settings(self,settype=''):
        self._command(f'settings {settype}')
        #init settings
        settings={'flash valid':True,'type':'RAM'}
        #get line
        line=self._textin.readline()
        #check for flash settings
        if('settings from flash' in line):
            settings['type']='flash'
            #get another line
            line=self._textin.readline()
        #check for invalid flash settings
        if line.startswith('Flash settings are invalid'):
            settings['flash valid']=False
            #get another line
            line=self._textin.readline()
        while(line and not line.startswith('>')):
            #split into name and value
            name,value=line.split(':')
            #strip spaces from name
            name=name.strip()
            #check for color
            if(name=='color'):
                vals=[int(v,16) for v in value.split()]
                value=(vals[0],tuple(vals[1:]))
            elif(name=='value'):
                value=int(value)
            else:
                #value is string, strip space chars
                value=value.strip()
            #add to dict
            settings[name]=value
            #get the next line
            line=self._textin.readline()

        return settings


    def get_ram_settings(self):
        settings = self._get_settings()
        self._set('ram_set',settings)

    def get_flash_settings(self):
        settings = self._get_settings(settype='flash')
        self._set('flash_set',settings)

    def write_settings(self):
        self._command('settings save')
        #get line
        line=self._textin.readline()
        while(line and not line.startswith('>')):
            line=self._textin.readline()
        self._clear('flash_set')
    
    def clear_settings(self):
        self._command('settings clear')
        #get line
        line=self._textin.readline()
        while(line and not line.startswith('>')):
            line=self._textin.readline()
        self._clear('flash_set')
    
    def get_altitude(self):
        self._command('alt')
        #get line
        line = self.get_line()
        #split name from value
        name, value = line.split(':')
        #strip spaces
        value = value.strip()
        #split out units
        value, units = value.split(' ')
        #return value
        self._set('flight_altitude', int(value))

    def set_altitude(self, val, units='meters'):
        #check units
        if units in ('meters', 'm'):
            #value already in meters
            pass
        elif units in ('feet', 'ft'):
            #convert ft to m
            val *= 0.3048
        else:
            raise ValueError(f'Unknown units \'{units}\'')
        #set value
        self._command(f'alt {int(val)}')

    def get_nightlight(self):
        self._command('nightlight')
        #get line
        line = self.get_line()
        #split line
        l, val = line.split(':')

        #strip whitespace
        val = val.strip()

        if val == 'on':
            self._set('nightlight',True)
        elif val == 'off':
            self._set('nightlight',False)
        else:
            raise RuntimeError(f'Unknown status \'{val}\'')

    def set_nightlight(self, val):
        #if value is bool, use strings
        if isinstance(val,bool):
            if val:
                val_str = 'on'
            else:
                val_str = 'off'
        else:
            #otherwise use string representation
            val_str = str(val)
        self._command(f'nightlight {val_str}')

    def reset(self,rtype):
        #reset types are in lower case
        rtype = rtype.lower()
        #send reset command
        self._command(f'rst {rtype}')

        line = self.get_line()

        if line.startswith('Error'):
            raise RuntimeError(line)

    def get_resets(self):
        #send resets command
        self._command('resets')

        line=self._textin.readline()
        number = None
        reason = None
        while(line and not line.startswith('>')):
            if line.startswith('Number of resets ='):
                l, value = line.split('=')
                number = int(value.strip())
            elif line.startswith('Reset reason :'):
                l, value = line.split(':')
                reason = value.strip()
            line=self._textin.readline()

        return number, reason

    def get_line(self):
        line=self._textin.readline()
        if(self.debug):
            print(f'Got line : \'{line}\'')
        return line
      
    def _command(self,cmd):
        '''low level command function to send command to the MSP430
        '''

        #trim extraneous white space from command
        cmd=cmd.strip()
            
        if(self.debug):
            print(f"sending '{cmd}'")

        #assemble string and encode to bytes
        cmd_b=(cmd+'\n').encode('utf-8')
        #send command
        self._sobj.write(cmd_b)

        #line buffer
        l='';

        #maximum number of iterations
        mi=3;

        #check command responses for echo
        while(cmd not in l):
            #get response
            l=self._textin.readline()
            
            #strip whitespace
            l=l.strip()
            
            if(self.debug and l):
                print(f"recived '{l}'")
            
            #subtract one from count
            mi-=1
            #check if we should timeout
            if(mi<=0):
                #throw error
                raise CommandError('Command response timeout')
            
        
