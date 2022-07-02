

info = {
     'off': {
         'name' : 'Off',
         'tag' : 'off',
         'short_description' : 'Turn all LEDs off.',
         'long_description' : 'Turn all LEDs off. This also turns off the regulator that controls the LEDs.',
     },
     'colortrain': {
         'name'  : 'Colortrain',
         'tag' : 'colortrain',
         'short_description' : 'Train of colors.',
         'long_description' : 'Train of three colors that moves up and down the rocket.'
     },
     'hue': {
         'name'  : 'Hue Fade',
         'tag' : 'hue',
         'short_description' : 'Smoothly fade through colors.',
         'long_description' : 'Smoothly fade through colors by varying the Hue.'
     },
     'burst': {
         'name'  : 'Burst',
         'tag' : 'burst',
         'short_description' : 'Burst pattern.',
         'long_description' : 'Burst pattern. This pattern is still in progress...'
     },
     'sat': {
         'name'  : 'Saturation Fade',
         'tag' : 'sat',
         'short_description' : 'Fade colors by fading to white.',
         'long_description' : 'Fade between colors by adjusting saturation. Hue is changed when saturation is zero (white). Colors are RGB and rotate across each LED string.'
     },
     'str_st': {
         'name'  : 'Static String',
         'tag' : 'str-st',
         'short_description' : 'Static color on each string.',
         'long_description' : 'Static color on each LED string. This pattern uses the current color list and only uses the first three colors in the list.'
     },
     'fs_gap': {
         'name'  : 'Flash with Gap',
         'tag' : 'fs-gap',
         'short_description' : 'Flash colors in list.',
         'long_description' : 'Flash colors in list. Turn off LEDs between colors.'
     },
     'boost': {
         'name'  : 'Boost',
         'tag' : 'boost',
         'short_description' : 'Bright flash at the start.',
         'long_description' : 'Bright flash of current color at the start of the pattern, then dimmer after that.'
     },
     'graph': {
         'name'  : 'Graph',
         'tag' : 'graph',
         'short_description' : 'Display a bar graph.',
         'long_description' : 'Display a bar graph, starting at the fins, the first few LEDs (set by the value parameter) are the current color, the rest are white.'
     },
     'day': {
         'name'  : 'Day',
         'tag' : 'day',
         'short_description' : 'Pattern for daytime.',
         'long_description' : 'Pattern for the daytime, light all LEDs but fins with the current color.'
     },
     'st_list': {
         'name'  : 'Static List',
         'tag' : 'st-list',
         'short_description' : 'Bands of color from list.',
         'long_description' : 'Fill non fin LEDs with colors from the current list. Length of bands are set by the value parameter. In night light mode, band width is fixed to one.'
     },
     'fs_nogap': {
         'name'  : 'Flash no Gap',
         'tag' : 'fs-nogap',
         'short_description' : 'Flash list colors without a gap.',
         'long_description' : 'Flash all colors in list without turning LEDs off between colors.'
     },
     'fl_list': {
         'name'  : 'Flow List',
         'tag' : 'fl-list',
         'short_description' : 'Flow list colors down LEDs.',
         'long_description' : 'Flow colors from color list, in order down the strips. Band width is defined by the value parameter. In night light mode, band width is fixed to one.'
     },
     'particle': {
         'name'  : 'Basic Particle',
         'tag' : 'particle',
         'short_description' : 'Falling particles.',
         'long_description' : 'Falling particles in the current color. Brightness of the tip of the particle is defined by brightness, the brightness of the trail starts at 5 and reduces to 1 by the end. Particles are spawned with a random speed and position above the nosecone. The number of particles is defined by the value parameter.'
     },
     'eyes_h': {
         'name'  : 'Eyes',
         'tag' : 'eyes-h',
         'short_description' : 'Eyes that appear and fade out.',
         'long_description' : 'A set of "eyes" are lit at a random position on each string (not in the fins). Each set of "eyes" are 2 red LEDs with a single LED between them.'
     },
     'wave_bu': {
         'name'  : 'Large Upwards Brightness Wave',
         'tag' : 'wave-bu',
         'short_description' : 'Large Brightness ripples moving up.',
         'long_description' : 'Upwards moving brightness ripples. The length of the ripple is defined by the value parameter. The brightness linearly ramps down by half the value parameter from the set brightness at the middle of the wave before linearly ramping back up. If the nosecone is used with the pattern, it\'s brightness ramps up and down with the LEDs at the top of the strip.'
     },
     'wave_bd': {
         'name'  : 'Large Downwards Brightness Wave',
         'tag' : 'wave-bd',
         'short_description' : 'Large Brightness ripples moving down.',
         'long_description' : 'Downwards moving brightness ripples. The length of the ripple is defined by the value parameter. The brightness linearly ramps down by half the value parameter from the set brightness at the middle of the wave before linearly ramping back up. If the nosecone is used with the pattern, it\'s brightness ramps up and down with the LEDs at the top of the strip.'
     },
     'wave_su': {
         'name'  : 'Small Upwards Brightness Wave',
         'tag' : 'wave-su',
         'short_description' : 'Small Brightness ripples moving up.',
         'long_description' : 'Upwards moving brightness ripples. The length of the ripple is defined by the value parameter. The brightness linearly ramps down by twice the value parameter from the set brightness at the middle of the wave before linearly ramping back up. If the nosecone is used with the pattern, it\'s brightness ramps up and down with the LEDs at the top of the strip.'
     },
     'wave_sd': {
         'name'  : 'Small Downwards Brightness Wave',
         'tag' : 'wave-sd',
         'short_description' : 'Small Brightness ripples moving down.',
         'long_description' : 'Downwards moving brightness ripples. The length of the ripple is defined by the value parameter. The brightness linearly ramps down by twice the value parameter from the set brightness at the middle of the wave before linearly ramping back up. If the nosecone is used with the pattern, it\'s brightness ramps up and down with the LEDs at the top of the strip.'
     },
     'hwave_d': {
         'name'  : 'Hue Wave Down',
         'tag' : 'hwave-d',
         'short_description' : 'Hue wave going down.',
         'long_description' : 'Downward shifting band that changes hue across the band. Band width is defined by the value parameter. The saturation and value of the LED colors are taken from the green and blue values from the current color, respectively.'
     },
     'hwave_u': {
         'name'  : 'Hue Wave Up',
         'tag' : 'hwave-u',
         'short_description' : 'Hue wave going up.',
         'long_description' : 'Upward shifting band that changes hue across the band. Band width is defined by the value parameter. The saturation and value of the LED colors are taken from the green and blue values from the current color, respectively.'
     },
     'swave_d': {
         'name'  : 'Saturation Wave Down',
         'tag' : 'swave-d',
         'short_description' : 'Saturation wave going down.',
         'long_description' : 'Downward shifting band that changes saturation across the band. Band width is defined by the value parameter. The hue and value of the LED colors are taken from the red and blue values from the current color, respectively'
     },
     'swave_u': {
         'name'  : 'Saturation Wave Up',
         'tag' : 'swave-u',
         'short_description' : 'Saturation wave going up.',
         'long_description' : 'Upward shifting band that changes saturation across the band. Band width is defined by the value parameter. The hue and value of the LED colors are taken from the red and blue values from the current color, respectively'
     },
     'ppanic': {
         'name'  : 'Power Panic',
         'tag' : 'ppanic',
         'short_description' : 'Panic pattern for power issues.',
         'long_description' : 'Panic pattern for power issues. This pattern will be triggered when the 5 V regulator for the LEDs goes out of regulation. This pattern will force the nosecone to also flash. This pattern shows an alternating pattern of red LEDs that flash on and off.'
     },
     'mpanic': {
         'name'  : 'Mode Panic',
         'tag' : 'mpanic',
         'short_description' : 'Altimiter mode panic.',
         'long_description' : 'Panic pattern used when the altimiter mode changes to a mode from an earlier flight phase. This pattern will force the nosecone to also flash. This pattern shows solid red flashing LEDs.'
     },
     'rpanic': {
         'name'  : 'Reset Panic',
         'tag' : 'rpanic',
         'short_description' : 'Unexpected reset panic.',
         'long_description' : 'Panic pattern used when the LED controller resets for an unexpected reason. This pattern will force the nosecone to also flash. This pattern shows solid yellow flashing LEDs.'
     },
     'ptpanic': {
         'name'  : 'Pattern Panic',
         'tag' : 'ptpanic',
         'short_description' : 'Invalid pattern panic',
         'long_description' : 'Panic pattern used when an invalid LED pattern is set. This pattern will force the nosecone to also flash. This pattern is solid flashing LEDs that alternate between red and yellow.'
     },
     'cparticle': {
         'name'  : 'Random Color Particle',
         'tag' : 'cparticle',
         'short_description' :'Falling particles of random colors.',
         'long_description' : 'Falling particles of random colors. Particles have a random hue and a random saturation that is between 128 and 255. Brightness of the tip of the particle is defined by brightness, the brightness of the trail starts at 5 and reduces to 1 by the end. Particles are spawned with a random speed and position above the nosecone. The number of particles is defined by the value parameter.'
     },
     'uparticle': {
         'name'  : 'Uniform Particle',
         'tag' : 'uparticle',
         'short_description' : 'Falling particles uniform around the rocket.',
         'long_description' : 'Falling particles in the current color. Each particle is repeated on all three strings. Brightness of the tip of the particle is defined by brightness, the brightness of the trail starts at 5 and reduces to 1 by the end. Particles are spawned with a random speed and position above the nosecone. The number of particles is defined by the value parameter.'
     },
     'cuparticle': {
         'name'  : 'Random Color Uniform Particle',
         'tag' : 'cuparticle',
         'short_description' : 'Falling particles of random colors.',
         'long_description' : 'Falling particles of random colors. Particles have a random hue and a random saturation that is between 128 and 255. Each particle is repeated on all three strings. Brightness of the tip of the particle is defined by brightness, the brightness of the trail starts at 5 and reduces to 1 by the end. Particles are spawned with a random speed and position above the nosecone. The number of particles is defined by the value parameter.'
     },
     'luparticle': {
         'name'  : 'List Color Uniform Particle',
         'tag' : 'luparticle',
         'short_description' : 'Falling particles with colors from the current list.',
         'long_description' : 'Falling particls with colors chosen randomly from the current color list. Each particle is repeated on all three strings. Brightness of the tip of the particle is defined by brightness, the brightness of the trail starts at 5 and reduces to 1 by the end. Particles are spawned with a random speed and position above the nosecone. The number of particles is defined by the value parameter.'
     },
     'lparticle': {
         'name'  : 'List Color Particle',
         'tag' : 'lparticle',
         'short_description' : 'Falling particles with colors from the current list.',
         'long_description' : 'Falling particls with colors chosen randomly from the current color list. Brightness of the tip of the particle is defined by brightness, the brightness of the trail starts at 5 and reduces to 1 by the end. Particles are spawned with a random speed and position above the nosecone. The number of particles is defined by the value parameter.'
     },
 }

