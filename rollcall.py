import xml.etree.ElementTree as ET
from time import time
from utils import get_congress_names
import os.path
import pickle
import datetime

def generate_rollcall_pickles(cong_ids, cats, force=False):
    """
    Force builds rollcall pickles for all congresses in list
    """
    print "generating pickles for %s congresses" % (len(cong_ids))
    mx = len(cong_ids)
    curr = 0
    for i in cong_ids:
        now = datetime.datetime.now().strftime("%H:%M")
        curr += 1
        print "Starting %s out of %s" % (curr, mx)
        print "It is now %s" % now
        load_rollcall(i, cats, silent=False, force_new = force)
    print "done."


def load_rollcall(congress_num, cats=None, silent=True, force_new=False):
    """
    Grabbing the data can be super expensive, thus, instead, we write the
    objects to file each time we create a new one and read the frozen one
    whenever there is a file that represents it already
    """
    fname = 'pickle/%s' % (congress_num)
    if not force_new and os.path.isfile(fname):
        f = open(fname)
        rc = pickle.load(f)
        f.close()
        return rc
    rc = RollCall(congress_num, cats, silent)
    f = open(fname, 'w')
    pickle.dump(rc, f)
    f.close()
    return rc

class RollCall(object):
    """
    roll call objects MUST be initialized with a congress number
    """

    house_votes = [[],[],[],[],[]]
    senate_votes = [[],[],[],[],[]]
    voters = None
    congress_num = None

    def convert_ids_to_people(self, ids):
        """Takes list of ids (as strings), returns list with ids replaced with people"""
        return [ self.voters[i] for i in ids ]

    def senate_yays(self):
        """Returns an array of senate voter ids representing yays"""
        return self.senate_votes[0]

    def house_yays(self):
        """Returns an array of house voter ids representing yays"""
        return self.house_votes[0]

    def senate_nays(self):
        """Returns an array of senate voter ids representing nays"""
        return self.senate_votes[1]

    def house_nays(self):
        """Returns an array of house voter ids representing nays"""
        return self.house_votes[1]

    def senate_attribs(self):
        """Returns an array of attribs represnting for each senate vote"""
        return self.senate_votes[4]

    def house_attribs(self):
        """Returns an array of attribs represnting for each house vote"""
        return self.house_votes[4]

    def __init__(self, congress_num, categories=None, silent=True):
        """
        roll call objects MUST be initialized with a congress number
        """
        if congress_num is None:
            raise Exception("You need to provide a congress number!!!")
        if categories is None:
            categories = ['passage', 'passage_part', 'amendment']
        self._collate_rollcalls(congress_num, categories, silent)
        self.voters = get_congress_names(congress_num)

    def _format_vote(self, filepath):
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

    def _get_specific_votes(self, congress_num, cats):
        """
        This filters for specific catergory of votes, used by __init__ -- you
        probably have no application outside of init for it
        """
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

    def _collate_rollcalls(self, congress_num, cats, silent=True):
        """
        This function is used by __init__ to generate the lists of votes for the
        house and senate, please don't use it directly
        """
        if not silent:
            print "Gathering valid votes (this is the longest part)"
        vote_files = self._get_specific_votes(congress_num, cats)
        num_votes = len(vote_files)
        if not silent:
            print "Processing %s votes:" % (num_votes)
        for f in vote_files:
            vote = self._format_vote(f)
            if vote[4]['where'] == 'senate':
                loc = self.senate_votes
            else:
                loc = self.house_votes
            for i in range(len(vote)):
                loc[i].append(vote[i])
            num_votes = num_votes - 1
            if not silent:
                print ": %s votes to go" % (num_votes)
