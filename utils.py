import simplejson
from urlgrabber import urlread
import xml.etree.ElementTree as ET

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

def get_congress_names(congress_num, names={}):
    person_attrs = ['firstname', 'lastname', 'middlename', 'religion',
            'nickname', 'state', 'gender', 'id']
    role_attrs = ['type','party']
    file_path = "data/%s/people.xml" % (congress_num)
    root_node = ET.parse(file_path).getroot()
    for person in root_node.iter('person'):
        person_id = person.attrib['id']
        if not names.has_key(person_id):
            attrs = {}
            for attr in person_attrs:
                attrs[attr] = person.attrib.get(attr,'NONE')
            role = person.find('role')
            for attr in role_attrs:
                attrs[attr] = role.attrib.get(attr,'NONE')
            names[person_id] = attrs
    return names 

def replace_names(congress_num, id_list):
    names = get_congress_names(congress_num)
    for i in range(len(id_list)):
        id = id_list[i]
        name = names.get(id)
        id_list[i] = name
    return id_list

def bench(func, *args, **kwargs):
    t1 = time()
    func(*args, **kwargs)
    return time()-t1

