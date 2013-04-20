import simplejson
from urlgrabber import urlread

def urljson_to_python(url):
    json_string = urlread(url)
    return simplejson.loads(json_string)

def get_count(base_url):
    if "?" in base_url:
        url = base_url + "&limit=0"
    else:
        url = base_url + "?limit=0"
    obj = urljson_to_python(url)
    return int(obj['meta']['total_count'])

def purge_on_attr(lst, attrs):
    '''Takes a list oflist of objs and a list of attrs. 
        Each attr is a dict containing:
            -attr name, the name on the object
            -type of matching, equals, not equals, in, not in
            -value to match
       returns filtered lst
    '''
    matching_funcs = []
    for a in attrs:
        if a['type'] == 'equals':
            f = lambda val: val[a['name']] == a['value']
        if a['type'] == 'not_equals':
            f = lambda val: not val[a['name']] == a['value']
        if a['type'] == 'in':
            f = lambda val: val[a['name']] in a['value']
        if a['type'] == 'not_in':
            f = lambda val: not val[a['name']] in a['value']
        matching_funcs.append(f)
        def matches(elm):
            for f in matching_funcs:
                if not f(elm):
                    return False
            return True
    new_list = [ e for e in lst if matches(e) ]
    return new_list


