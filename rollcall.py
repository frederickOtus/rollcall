from utils import urljson_to_python as dl, get_count, purge_on_attr as purge

vote_url = "http://www.govtrack.us/api/v2/vote"
key_mapping = {'+':0, '-':1, '0':2, 'P':3}

def congress_votes(congress_num):
    url = vote_url + "?congress=%s" % (congress_num)
    count = get_count(url)
    url += "&limit=%s" % (count)
    votes = dl(url)['objects']
    return votes

def collate_voters(congress_num):
    import time
    t1 = time.time()
    votes = congress_votes(congress_num)
    print len(votes)
    atr = [{'name':'category', 'type':'in', 'value':['passage',
        'passage_part']},]
    purged = purge(votes, atr)
    ids = [ str(p['id']) for p in purged ]
    id_str = '|'.join(ids)

    count_url = "http://www.govtrack.us/api/v2/vote_voter?vote__in=%s" % (id_str)
    count = get_count(count_url)
    url = "http://www.govtrack.us/api/v2/vote_voter?limit=%s&vote__in=%s" % (count, id_str)
    member_votes = dl(url)['objects']
    collated_votes = {}
    print len(member_votes)
    for vote in member_votes:
        vote_id = vote['vote']['id']
        key = vote['option']['key']
        member = vote['person']['id']
        if not collated_votes.has_key(vote_id):
            collated_votes[vote_id] = [[],[],[],[]]
        key_index = key_mapping[key]
        collated_votes[vote_id][key_index].append(member)
    print "time= %s" % (time.time()-t1)
    return collated_votes
