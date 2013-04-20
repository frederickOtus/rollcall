import xml.etree.ElementTree as ET
from time import time

def format_vote(filepath):
    """Takes a filepath to a rollcall vote and returns a 1 dimensional array
    with 5 rows, the first four are arrays of the ids of congresspersons who voted
        -for
        -against
        -abstain
        -were not present
    The last is a dictionary of attributes
    """
    vote_mapping = {'+': 0, '-':1, "P":2,"0":3}
    #this is a mapping of the symbols used to represent votes to which
    #array we are using to track that vote type
    extra_attrs = ['category','question','result','type']
    #Extra nodes hat we want to pull content from
    root = ET.parse(filepath).getroot()
    attrs = root.attrib
    for a in extra_attrs:
        attrs[a] = root.find(a).text

    formatted_data = [[],[],[],[],[]]

    for voter in root.iter('voter'):
        v_id = voter.attrib['id']
        vote_sym = voter.attrib['vote']
        vote_indx = vote_mapping[vote_sym]
        formatted_data[vote_indx].append(v_id)

    formatted_data[4] = attrs #the last elm is an array of attributes about the
                              # rollcall

    return formatted_data    

def bench(func, *args, **kwargs):
    t1 = time()
    func(*args, **kwargs)
    return time()-t1

def get_specific_votes(congress_num, cats):
    from os import listdir
    from os.path import isfile, join
    #these are some filepath things we use to find the files we care about

    vote_path = 'data/%s/rolls' %(congress_num)
    def is_valid_file(f):
        if not isfile(join(vote_path,f)):
            return False
        xml_root = ET.parse("%s/%s" %(vote_path, f)).getroot()
        category = xml_root.find('category').text
        return category in cats

    files = [ "%s/%s" % (vote_path, f) for f in listdir(vote_path) if is_valid_file(f) ]
    return files 

def collate_rollcalls(congress_num, cats):
    collated_votes = [[],[],[],[],[]]
    vote_files = get_specific_votes(congress_num, cats)
    num_votes = len(vote_files)
    print "Processing %s votes:" % (num_votes)
    for f in vote_files:
        vote = format_vote(f)
        for i in range(len(vote)):
            collated_votes[i].append(vote[i])
        num_votes = num_votes - 1
        print ": %s votes to go" % (num_votes)
    return collated_votes
        
if __name__ == "__main__":
    print "Bench marking collate_rollcalls()....."
    print bench(collate_rollcalls, 112, ["passage",])
