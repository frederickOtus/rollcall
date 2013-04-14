from utils import urljson_to_python as dl, get_count, purge_on_attr as purge

vote_url = "http://www.govtrack.us/api/v2/vote"

def congress_votes(congress_num):
    url = vote_url + "?congress=%s" % (congress_num)
    count = get_count(url)
    print count
    url += "&limit=%s" % (count)
    votes = dl(url)['objects']
    return votes

def collate_voters(congress_num):
    votes = congress_votes(congress_num)
    atr = [{'name':'category', 'type':'in', 'value':['passage',
        'passage_part']},]
    return purge(votes, atr)

        

