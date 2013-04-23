from rollcall import load_rollcall
import pickle
import os

def load_rules(congress_num, force_new=False, **kwargs):
    """
    Grabbing the data can be super expensive, thus, instead, we write the
    objects to file each time we create a new one and read the frozen one
    whenever there is a file that represents it already
    """
    fname = 'pickle/%s.rules' % (congress_num)
    if os.path.isfile(fname) and not force_new:
        print fname
        f = open(fname)
        rules = pickle.load(f)
        f.close()
        return rules
    rules = Rules(congress_num, **kwargs)
    f = open(fname, 'w')
    pickle.dump(rules, f)
    f.close()
    return rules
   
def leaders(congress_num):
    """Grabs the most important people and their sway in descending order"""
    rules = load_rules(congress_num)
    leaders_dict = rules.most_influential()
    keys = [ key for key, val in leaders_dict.items() ]
    peoples = rules.resolve_names(keys)
    leaders = []
    for i in range(len(keys)):
        peoples[i]['influence'] = leaders_dict[keys[i]]
        leaders.append(peoples[i])
    return sorted(leaders, key=lambda leader: -leader['influence'])

class VotingCluster(object):
    """ The apriori develops implication parings, ie: Sen McCain votes for X, so
    these 5 senators will as well. You can have any number of leaders and
    delegates. This object represents that grouping."""

    leaders = None
    delegates = None
    confidence = None
    _diversity = None
    _majority_party = None

    def __init__(self, leaders, delegates, confidence, namer):
        leaders = namer(list(leaders))
        delegates = namer(list(delegates))
        self.leaders = leaders
        self.delegates = delegates
        self.confidence = confidence
        self._diversity = None
        self._majority_party = None

    def party_diversity(self):
        """diversity is represented by what percentage of the block is composed
        of non-majority party members"""
        if self._diversity is None:
            block_size = len(self.delegates) + len(self.leaders)
            party_rep = {}
            largest = ('', 0)
            for member in self.leaders + self.delegates:
                party = member['party']
                party_rep[party] = party_rep.get(party, 0) + 1
                if largest[1] < party_rep[party]:
                    largest = (party, party_rep[party])
            self._diversity = 1.0 - (largest[1] / block_size)
            self._majority_party = largest[0]
        return self._diversity

    def majority_party(self):
        """Returns the dominant party of this cluster"""
        if self._majority_party is None:
            self.party_diversity()
        return self._majority_party

class Rules(object):
    """
    I'm using an object to represent the data for the simple benefit of being
    able to easily use pickle to serialize results. It also helps to simplify
    interactions with underlying data structures
    """

    data = None
    rules = None
    L = None
    suppData = None
    congress_num = None
    _leaders = None
    clusters = None

    def __init__(self, congress_num, min_support = .48, min_conf = .95):
        """
        Takesa congress number and does all of the apriori nonsense on it then
        stores results
        """
        rc = load_rollcall(congress_num)
        self.data = rc.senate_yays()
        print len(self.data)
        l, sd = apriori(self.data, min_support)
        self.congress_num = congress_num
        self.L = l
        self.support_data = sd
        self.rules = generateRules(self.L, self.support_data, min_conf)
        self.clusters = []
        self.rc = load_rollcall(self.congress_num)
        for rule in self.rules:
            self.clusters.append(VotingCluster(rule[0],rule[1],rule[2],
                self.resolve_names))
                                        #TODO fix this ugly hack: i have to pass
                                        #a reference to a class function due to
                                        #poor oversight
                                        

    def most_influential(self):
        """
        The apriori sort does a lot of implications, that is, if
        congressperson votes on x, then you can expect set y of other
        congresspersons to do so as well. This simple finds how many
        other congresspersons a single congressperson has sway over by
        taking len of the set of all people he/she had a hand in influencing
        """
        if not self._leaders is None:
            return self._leaders
        lead_count = {}
        leaders = frozenset()
        
        for rule in self.rules:
            leaders = leaders.union(rule[0])

        def get_count(ldr):
            tmp = frozenset()
            for rule in self.rules:
                if ldr in rule[0]:
                    tmp = tmp.union(rule[1])
            return len(tmp)

        for leader in list(leaders):
            lead_count[leader] = get_count(leader)

        self._leaders = lead_count
        return lead_count
    
    def resolve_names(self, val):
        """Takes a list or single id and returns their person dict"""
        if type(val) == type("") or type(val) == type(3):
            return self.rc.convert_ids_to_people([val,])[0]
        elif type(val) == type([]):
            return self.rc.convert_ids_to_people(val)
        raise Exception('Derp? needs to be int/str/array/dict<key is id>')

def createC1(dataSet):
    C1 = []
    for transaction in dataSet:
        for item in transaction:
            if not [item] in C1:
                C1.append([item])
    C1.sort()
    return map(frozenset, C1)

def scanD(D, Ck, minSupport):
    ssCnt = {}
    for tid in D:
        for can in Ck:
            if can.issubset(tid):
                if not ssCnt.has_key(can):
                    ssCnt[can] = 1
                else:
                    ssCnt[can] += 1
    numItems = float(len(D))
    retList = []
    supportData = {}
    for key in ssCnt:
        support = ssCnt[key]/numItems
        if support >= minSupport:
            retList.insert(0,key)
        supportData[key] = support
    return retList, supportData

def aprioriGen(Lk, k): #creates Ck (what)
    retList = []
    lenLk = len(Lk)
    for i in range(lenLk):
        for j in range(i+1, lenLk):
            L1 = list(Lk[i])[:k-2]
            L2 = list(Lk[j])[:k-2]
            L1.sort()
            L2.sort()
            if L1 == L2:
                retList.append(Lk[i] | Lk[j])
    return retList

def apriori(dataSet, minSupport = 0.5):
    C1 = createC1(dataSet)
    D = map(set, dataSet)
    L1, supportData = scanD(D, C1, minSupport)
    L = [L1]
    k = 2
    while (len(L[k-2]) > 0):
        Ck = aprioriGen(L[k-2],k)
        Lk, supK = scanD(D, Ck, minSupport)
        supportData.update(supK)
        L.append(Lk)
        k += 1
    return L, supportData

def generateRules(L, supportData, minConf=0.7):
    bigRuleList = []
    for i in range(1, len(L)):
        for freqSet in L[i]:
            H1 = [frozenset([item]) for item in freqSet]
            if (i>1):
                rulesFromConseq(freqSet, H1, supportData, bigRuleList, minConf)
            else :
                calcConf(freqSet, H1, supportData, bigRuleList, minConf)
    return bigRuleList

def calcConf(freqSet, H, supportData, br1, minConf = 0.7):
    prunedH = []
    for conseq in H:
        conf = supportData[freqSet]/supportData[freqSet-conseq]
        if conf >= minConf:
            print freqSet-conseq, '-->', conseq,'conf:',conf
            br1.append((freqSet-conseq,conseq, conf))
            prunedH.append(conseq)
    return prunedH

def rulesFromConseq(freqSet, H, supportData, br1, minConf = 0.7):
    m = len(H[0])
    if (len(freqSet) > (m+1)):
        Hmp1 = aprioriGen(H, m + 1)
        Hmp1= calcConf(freqSet, Hmp1, supportData, br1, minConf)
        if (len(Hmp1) > 1):
            rulesFromConseq(freqSet, Hmp1, supportData, br1, minConf)
