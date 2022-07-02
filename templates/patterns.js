
const NightKnight_patterns = {
{% for pn,p in patterns.items() %}
    {{ pn }}: {
    {% for k,v in p.items() %}
        {{ k }}: "{{ v }}",
    {% end %}
    },
{% end %}
}
