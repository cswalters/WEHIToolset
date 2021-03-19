


def main():

    convref = '/Users/chris/Documents/WEHI/CisSocs/Networks/Data/GSTCisSocsPulldown/UniprotAccToIDGSTSocs.csv'
    datafile = '/Users/chris/Documents/WEHI/CisSocs/Networks/Data/GSTCisSocsPulldown/CleanModPullData.txt'

    entries, data = get_uniprot_entries(convref, datafile)

    result = match_ids(entries, data)

    write_results(result)

    return


def get_uniprot_entries(conversion, datafile):

    entries = {}

    with open(conversion) as c:
        raw = c.read().split("\n")

        for x in raw:
            entries[x.split(",")[0]] = x.split(",")[1]

    with open(datafile) as d:
        data = d.read().split("\n")

    return entries, data


def match_ids(entries, data):

    orig_ids = [x.split('\t')[14] for x in data]

    for i in range(len(orig_ids)):

        for j in orig_ids[i].split(";"):
            if j in entries.keys():
                data[i] += "\t" + entries[j]
                break

    return data

def write_results(results):

    resultsref = 'Output/Results.txt'

    with open(resultsref, "w") as r:
        r.write("\n".join(results))


if __name__ == '__main__':
    main()
