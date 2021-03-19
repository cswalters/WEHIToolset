import sys
from splinter import Browser


# Sample file formats:
#   - Note that the program automatically skips the first line of teh file to accommodate for column headers.

#   Sample input (as .csv file):
"""
    "OfficialGeneSymbol","EnsemblID"
    "A2M","ENSG00000175899"
    "AARS","ENSG00000090861"
    "ABCE1","ENSG00000164163"
    "ABL1","ENSG00000097007"
    "ABL2","ENSG00000143322"
"""

#   Sample output (as Results.csv):
"""
    "OfficialGeneSymbol","EnsemblID","Jak-STAT","MAPK Signaling Pathway"
    "A2M","ENSG00000175899","Jak-STAT","MAPK Signaling Pathway"
    "AARS","ENSG00000090861","Jak-STAT",
    "ABCE1","ENSG00000164163",,
    "ABL1","ENSG00000097007",,"MAPK Signaling Pathway"
    "ABL2","ENSG00000143322","Jak-STAT",
"""


# Minimum number of proteins required to be in a path for it to be processed by get_assoc_paths().
MIN_PROT_IN_PATH = 10

# Maximum number of pathways to be processed by get_enrich_paths().
MAX_NUM_PATHS = 20

# Keywords for identification of significant paths.
KEYWORDS = ['signaling pathway', 'differentiation', 'junction', 'apoptosis',
            'natural killer', 'cytokine', 'phagocytosis', 'endocytosis',
            'adhesion', 'activation', 'hemapoietic']


def main():

    # Validates and verifies command line arguments given.
    if len(sys.argv) != 3 or str(sys.argv[2]) not in ["0", "1"]:
        print("Insufficient or invalid command line arguments.\nPlease consult the "
              "Readme.txt for format and relevance of required arguments.")
        return

    # Stores filepath of list of gene symbols and Ensembl IDs.
    fileref = "Data/" + sys.argv[1]

    # Determines whether associated or enriched pathways are to be extracted from gene list.
    if int(sys.argv[2]):
        pathways = get_enriched_paths(get_gene(fileref, "ensembl"))
    else:
        pathways = get_assoc_paths(get_gene(fileref))

    # Stores extracted pathways in .csv document as each gene and
    # the pathways (of those extracted) that it is involved in.
    write_refined_results(get_gene(fileref), pathways)

    return


def get_gene(fileref, standard="symbol"):

    geneList = []

    # Opens file and depending on value of parameter 'standard,' either
    # extracts Offical Gene Symbols or Ensembl IDs
    with open(fileref) as f:
        if standard == "symbol":
            geneList = [x.split(",")[0] for x in f.read().split("\n")[1:]]
        elif standard == "ensembl":
            geneList = [x.split(",")[1] for x in f.read().split("\n")[1:]]

    return geneList


def get_assoc_paths(genelist):

    links = []
    pathwayList = []

    # URL to KEGG Colour&Search pathway search tool.
    url = "http://www.genome.jp/kegg/tool/map_pathway2.html"

    # Initialises a headless browser instance using Chrome Webdriver.
    with Browser('chrome', headless=True) as browser:

        browser.visit(url)

        # Fills form with desired gene list and submits it.
        browser.fill("org", "hsa")
        browser.fill("unclassified", "\n".join(genelist))
        browser.find_by_value("Exec").click()

        # Check to determine if gene list was accepted.
        if browser.is_text_not_present("Pathway Search Result"):
            print("Pathway lookup failed.")

        # Extracts list of all pathways
        pathways = browser.find_by_tag("li")

        # Iterates through each patwhay in list and extracts contained link if
        # the number of proteisn from gene list exceeds MIN_NUM threshold designated at start of script.
        for i in range(len(pathways)):
            if int(pathways[i].find_by_tag("a")[1].text) > MIN_PROT_IN_PATH:
                links.append(pathways[i].find_by_tag("a").first)
            else:
                break

        # Iterates through list of pathway links to extract list of genes associated with pathway.
        for i in links:

            # Ensures pathway associated with either keywords/functions/areas of interest
            pursue = False

            for word in KEYWORDS:
                if word.upper() in i.text.upper():
                    pursue = True

            if not pursue:
                continue

            # Opens pathway link in new window and traverses to pathway information entry in KEGG database.
            with Browser("chrome", headless=True) as newTab:

                newTab.visit(i['href'])
                newTab.find_link_by_text("Pathway entry").click()

                # Iterates through data on KEGG pathway entry page until row containing associated genes found.
                for j in newTab.find_by_name("form1").find_by_tag("table").find_by_tag("table").find_by_tag("tr"):

                    if "Gene" in j.text:

                        # Extracts genes and pathway name to pathwayList variable as a tuple.
                        newTabText = j.text.split("\n")[1:]
                        genes = [newTabText[x].split(";")[0] for x in range(len(newTabText)) if x % 2 == 1]

                        pathwayName = " ".join(i.text.split(" - ")[0].split(" ")[1:])

                        pathwayList.append((pathwayName, genes))

                        break

    return pathwayList


def get_enriched_paths(genelist):

    count = 0
    pathwayList = []

    # URL to DAVID - NIH Functional Annotation Tool
    url = "https://david.ncifcrf.gov/summary.jsp"

    # Initialises a headless browser instance using Chrome Webdriver.
    with Browser("chrome") as browser:

        browser.visit(url)

        # Upload gene list, designate it as Ensembl IDs and submit web form.
        browser.fill("pasteBox", "\n".join(genelist))
        browser.find_by_id("IDT").first.select("ENSEMBL_GENE_ID")
        browser.choose("rbUploadType", "list")

        browser.find_by_value("Submit List").click()

        # Switch to functional annotations analysis as chart
        browser.find_by_xpath('//*[@id="summaryTree"]/li[7]/a').first.click()
        chartTypes = browser.find_by_xpath('//*[@id="summaryTree"]/li[7]/ul/li/table/tbody').find_by_tag("tr")

        # Select KEGG chart
        for chart in chartTypes:
            if "KEGG" in chart.text:
                chart.find_by_value("Chart").first.click()
                break

        # Switch windows
        browser.windows.current = browser.windows[-1]

        # Extract and iterate through pathways in KEGG chart
        pathways = browser.find_by_xpath('//*[@id="row"]/tbody').find_by_tag("tr")

        for path in pathways:

            # Ensure no more than 15 pathways are extracted
            if count >= MAX_NUM_PATHS:
                break

            # Ensures pathway associated with either keywords/functions/areas of interest
            pursue = False

            for word in KEYWORDS:
                if word.upper() in path.text.upper():
                    pursue = True

            if not pursue:
                continue

            # Store pathway name.
            fullName = path.text

            # Initialise new browser instance to navigate to KEGG pathway entry.
            with Browser("chrome", headless=True) as newTab:

                # Navigate to KEGG database pathway entry.
                newTab.visit(path.find_by_tag("a").first["href"])
                newTab.visit(newTab.find_link_by_partial_href("www.genome.jp/dbget-bin/show_pathway").first['href'])
                newTab.find_link_by_text("Pathway entry").click()

                # Extract genes associated with pathway from Gene row in KEGG pathway entry.
                for j in newTab.find_by_name("form1").find_by_tag("table").find_by_tag("table").find_by_tag("tr"):

                    if "Gene" in j.text:

                        newTabText = j.text.split("\n")[1:]
                        genes = [newTabText[x].split(";")[0] for x in range(len(newTabText)) if x % 2 == 1]

                        pathName = " ".join(fullName.split(" RT")[0].split(" ")[1:])

                        pathwayList.append((pathName, genes))

                        break

            # Increment count to track pathways extracted.
            count += 1

    return pathwayList


def write_raw_results(pathways):

    # Creates a .csv record for each pathway recording OfficialGeneSymbol of each associated
    # gene in the first column and the pathway name in the second column.
    for entry in pathways:

        with open("Data/Pathways/" + entry[0] + ".csv", "w") as record:
            record.write("OfficialGeneSymbol," + entry[0])

            # Writes each gene entry
            for g in entry[1]:
                record.write("\n" + g + "," + entry[0])


def write_refined_results(genelist, pathways):

    count = 0
    output = {"OfficialGeneSymbols": []}

    # Initialise dictionary entries for each gene in inputted gene list
    for gene in genelist:
        output[gene] = []

    # Initialise the number of pathway columns for each dictionary entry
    for key in output.keys():
        for i in range(len(pathways)):
            output[key].append("")

    # Iterate through each pathway and tehn each gene in each pathway and record the
    # pathway for the relevant genes in dictionary of the inputted gene list.
    for entry in pathways:
        output["OfficialGeneSymbols"][count] = entry[0]

        for g in entry[1]:
            if g in output:
                output[g][count] = entry[0]

        count += 1

    # Write resultant dictionary to output Results.csv file.
    with open("Data/Pathways/Results.csv", "w") as results:
        for key in output.keys():
            results.write(key + "," + ",".join(output[key]) + "\n")


if __name__ == "__main__":
    main()
