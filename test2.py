#Andre's Messy Code....
from igraph import *
import matplotlib.pyplot as plt
import matplotlib as mpl
from collections import Counter
import numpy as np
import csv
import operator
import time
import pickle
#from wordcount import clean
from wordcloud import WordCloud
import psycopg2
import re
from bs4 import BeautifulSoup


# NOTE TO SELF:
# FALSE == 0, TRUE != 0
#USER = RED, THREAD = BLUE

def buildGraph(sizeLimit=False, limitNum=500, save=False):
    usernameDict = {}
    tidDict = {}
    vertex_counter = 0
    edge_counter = 0
    break_counter = 1
    g = Graph()
    
    with open('post_hackthissite.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=' ')
        dataSize = 43783 #WARNING: this number is only for the 'post_hackthissite.csv
        #print(dataSize)
        currentIter = 0
        for row in reader:
            rowList = row[0].split(',')
            #print(rowList)
            if rowList[0] != 'tid': #skips title row (first row)
                if rowList[1] not in usernameDict:
                    g.add_vertices(1)
                    g.vs[vertex_counter]["type"] = 0
                    # g.vs[vertex_counter]["color"] = "red"
                    g.vs[vertex_counter]["idx"] = "uid_" + rowList[1]
                    usernameDict[rowList[1]] = vertex_counter
                    vertex_counter += 1
                if rowList[0] not in tidDict:
                    g.add_vertices(1)
                    g.vs[vertex_counter]["type"] = 1
                    # g.vs[vertex_counter]["color"] = "blue"
                    g.vs[vertex_counter]["idx"] = "tid_" + rowList[0]
                    tidDict[rowList[0]] = vertex_counter
                    vertex_counter += 1
                g.add_edge(usernameDict[rowList[1]], tidDict[rowList[0]])
                g.es[edge_counter]["weight"] = int(rowList[2])   
                edge_counter += 1
                
                if sizeLimit:
                    if break_counter == limitNum:
                        break
                    break_counter += 1
                else:#PROGRESS BARS for my sanity
                    if currentIter == int(dataSize/4):
                        print("25% of graph built")
                    elif currentIter == int(dataSize/2):
                        print("50% of graph built")
                    elif currentIter == int(dataSize * 0.75):
                        print("75% of graph built")
                    currentIter += 1
    
    print("Built Graph 100 percent: --- %s seconds ---" % (time.time() - start_time))
    summary(g)
    # print("Is G weighted:", "yes" if g.is_weighted() else "no")
    
    # layout = g.layout("kk")
    # plot(g, vertex_color=[color for color in g.vs["color"]], edge_width = [weight for weight in g.es["weight"]])
    # plot(g, vertex_color=[color for color in g.vs["color"]], vertex_label=[name for name in g.vs["idx"]], edge_width = [weight for weight in g.es["weight"]], edge_label = [weight for weight in g.es["weight"]])
    # plot(g, layout = layout, vertex_color=["red" if type == 0 else "blue" for type in g.vs["type"]], edge_width = [weight for weight in g.es["weight"]])
    # plot(g, vertex_color=["red" if type == 0 else "blue" for type in g.vs["type"]], edge_width = [weight for weight in g.es["weight"]])

    if save:
        g.write_pickle('save.pickle', version=2)
        # pickle.dump(g, open("save.p", "wb"))
        print("Graph saves to pickle file!")
    
    return g
    

#test function for me for misc purposes
def algoTest(g, func=None):
    if func == "fastGreedy":
        dendro = g.community_fastgreedy(weights="weight")
        # print(dendro)
        summary(dendro)
        print(dendro.optimal_count)
        dendroClusters = dendro.as_clustering(n=6)
        print(len(dendroClusters))
        
        # dendroClustersSorted = sorted(dendroClusters, key = len, reverse = True)
        '''
        file = open('fastGreedy_cluster_list_Weights.txt', 'w')
        file.write("List of clusters using fastgreedy algoirthm with weights:\n")
        file.write("-----------------------------------------------------\n")
        for item in dendroClustersSorted:
            # file.write(str(item) + "\n")
            writeStr = ""
            for id in item:
                writeStr += g.vs[id]["idx"] + " "
            file.write(writeStr + "\n")
                
        file = open('fastGreedy_cluster_lenghts.txt', 'w')
        for cluster in dendroClustersSorted:
            file.write(str(len(cluster)) + "\n")
        '''
    elif func == "Top1%":
        #top 1% of degree code:
        degrees_of_users = []
        for i, vertex in enumerate(g.vs):
            #print(i, vertex)
            if g.vs[i]["type"] == 1:
                degrees_of_users.append((vertex["idx"], g.degree(i)))
                
        # degrees_of_users.sort(key=lambda x: x[1]) ......sorting method below is faster?
        degrees_of_users.sort(key=operator.itemgetter(1), reverse=True)
        topPercentNum = int(len(degrees_of_users)/100)
        
        print("Top 1% of threads with highest degree")
        for i in range(topPercentNum):
            print(str(i) + ") " + str(degrees_of_users[i]))
        
        # double check result
        # print("All users degree:")
        # for element in degrees_of_users:
            # print(element[1])
            
    elif func == "getPostContentFromEdgeList":
        DBname = "MichalisPrj"
        pword = "1"
        tableName = "tbl_hackthissite_post"
        con = psycopg2.connect(database=DBname, user = "postgres", password=pword) #connect to postgres
        curs = con.cursor()
        
        for i in range(1,7):
        
            file = open('graph-and-edges\select_six_dege_{}.txt'.format(i), 'r')
            clusterEdgeList = file.read().split('\n')
            
            file = open('select_six_post_content_{}.txt'.format(i), 'wb')
            
            for edge in clusterEdgeList:
                edgePair = sorted(edge.split(','))
                if len(edgePair) == 2:
                    tid = edgePair[0]
                    uid = edgePair[1]
                    # print(uid, tid)
                    
                    ExecuteStatement = "SELECT post_content FROM " + tableName + " WHERE uid = '{}' ".format(uid[4:]) + "AND tid = '{}'".format(tid[4:])
                    #when searching for a uid and tid, all posts that that user has in that forum is considered. 
                    #for exapme: uid = 6425 and tid = 212 has 9 posts in total.
                    #they are all taken into account when analyzing the topic of 'select_six_dege_1.txt'
                    curs.execute(ExecuteStatement)
                    postList = curs.fetchall()
                    for post in postList:
                    # print(str(post_content))
                    # print("length: " + str(len(post_content)))
                    # print("uid: " + str(uid))
                    # print("tid: " + str(tid))
                        cleanStr = clean(str(post))
                        cleanStr = cleanStr[3:-4]
                        # cleanStr = str(cleanStr.encode("utf-8")).
                        #Remove the unicode space in the file
                        file.write(bytes(cleanStr + "\n", encoding="utf-8"))
            
            print("Done with {}".format(i))
    
    # elif func == "wordcloud":
         # for i in range(1,7):
            # file = open('select_six_post_content_{}.txt'.format(i), 'r', encoding="utf-8")
            # stopWordsFile = open('stopwords.txt', 'r')
            
            # fig = plt.figure(figsize=(20, 10))
            # ax  = fig.add_subplot('111')
            
            # wcloud = WordCloud(background_color="white", mode = "RGB", width=2000, height = 1000, stopwords = stopWordsFile.read().split('\n')).generate(file.read())
            # plt.title("wordcloud_{}".format(i))
            # plt.imshow(wcloud)
            # plt.axis("off")
            # fig.tight_layout()
            # fig.savefig('select_six_wordplot_{}.png'.format(i))
    
    # elif func == "wordcloud2":
        # DBname = "MichalisPrj"
        # pword = "1"
        # tableName = "tbl_hackthissite_post"
        # con = psycopg2.connect(database=DBname, user = "postgres", password=pword) #connect to postgres
        # curs = con.cursor()
        
        # for num in range(3,4):
            # c1 = pickle.load(open("graph-and-edges\select_six_{}.pickle".format(num), "rb"))
            # c1_degreeList = c1.degree()
            # total = np.sum(c1_degreeList)
            # degreeList = []
            
            # for i, degree in enumerate(c1_degreeList):
                # percentage = (degree/total)*100
                # if c1.vs[i]["type"] == 1:
                    # degreeList.append((percentage, c1.vs[i]["idx"]))
                    
            # degreeList.sort(key=operator.itemgetter(0), reverse=True)
            
            # plotString = ""
            
            # 1 has 9 significant threads
            # 2 has 16 significant threads
            # 3 has 12 significant threads EXCLUDING the first one (outlier)
            # 4 has 5 significant threads
            # 5 has 10 significant threads
            # 6 has 11 significant threads
            
            # fix this later to actually calculate the significant number of threads
            # significant_threads = 12
            
            # for strng in degreeList[1:significant_threads]:
                # tid = strng[1][4:]
                # ExecuteStatement = "SELECT post_content FROM " + tableName + " WHERE tid = '{}'".format(tid)
                # curs.execute(ExecuteStatement)
                # postList = curs.fetchall()
                # for post in postList:
                    # cleanStr = clean(str(post))
                    # cleanStr = cleanStr[3:-4]
                    # plotString += cleanStr + "\n"
                
            
            # stopWordsFile = open('stopwords.txt', 'r')
            
            # fig = plt.figure(figsize=(20, 10))
            # ax  = fig.add_subplot('111')
            
            # wcloud = WordCloud(background_color="white", mode = "RGB", width=2000, height = 1000, stopwords = stopWordsFile.read().split('\n')).generate(plotString)
            # plt.title("wordcloud_{}".format(num))
            # plt.imshow(wcloud)
            # plt.axis("off")
            # fig.tight_layout()
            # fig.savefig('significant_threads_wordplot_{}.png'.format(num))
    
    elif func == "vertexDegreeDistribuion":
        for i in range(1,7):
            c1 = pickle.load(open("graph-and-edges\select_six_{}.pickle".format(i), "rb"))
            filename = "cluster_{}_vertex_degree_distribution_tid.png".format(i)
            summary(c1)
            c1_degreeList = c1.degree()
            total = np.sum(c1_degreeList)
            # printList = []
            x = []
            y = []
            x2 = []
            y2 = []
            
            for i, degree in enumerate(sorted(c1_degreeList)):
                percentage = (degree/total)*100
                if c1.vs[i]["type"] == 0:
                    x.append(i)
                    y.append(percentage)
                else:
                    x2.append(i)
                    y2.append(percentage)
                # if percentage > 1:
                    # printList.append(c1.vs[i]["idx"])
                    # printList.append(str(percentage) + "%")
            
            fig = plt.figure(figsize=(8, 6))
            ax = fig.add_subplot(111)
            
            ax.plot(x2, y2, 'bo')
            ax.set_xlabel('num')
            ax.set_ylabel('percentage')
            
            fig.tight_layout()
            fig.savefig(filename)
            
    elif func == "printSigThreads":
        DBname = "MichalisPrj"
        pword = "1"
        tableName = "tbl_hackthissite_post"
        con = psycopg2.connect(database=DBname, user = "postgres", password=pword) #connect to postgres
        curs = con.cursor()
        
        for num in range(1,7):
            c1 = pickle.load(open("graph-and-edges\select_six_{}.pickle".format(num), "rb"))
            c1_degreeList = c1.degree()
            total = np.sum(c1_degreeList)
            degreeList = []
            
            for i, degree in enumerate(c1_degreeList):
                percentage = (degree/total)*100
                if c1.vs[i]["type"] == 1:
                    degreeList.append((percentage, c1.vs[i]["idx"]))
                    
            degreeList.sort(key=operator.itemgetter(0), reverse=True)
            
            plotString = ""
            
            #1 has 6 significant threads
            #2 has 3 significant threads
            #3 has 5 significant threads EXCLUDING the first one (outlier)
            #4 has 6 significant threads
            #5 has 7 significant threads
            #6 has 6 significant threads
            sig_num_threads_dict = {
                1: [0,6],
                2: [0,3],
                3: [1,6], #1 for the outlier, six to push everything back by 1
                4: [0,6],
                5: [0,7],
                6: [0,6],
            }
            #fix this later to actually calculate the significant number of threads
            
            print("Clutser {}:".format(num))
            for strng in degreeList[sig_num_threads_dict[num][0]:sig_num_threads_dict[num][1]]:
                tid = strng[1][4:]
                print("\t" + tid)
                
    elif func == "special":
        print("temporary")
        
    else:
        print("No function was chosen for function algoTest().")
        print("In the parameter of the function please specify \'func=(functionName)\' ")
    '''
    #write to file code
    c = g.community_infomap()
    file = open('infoMap_cluster_list.txt', 'w')
    file.write("List of clusters using infomap algoirthm:\n")
    file.write("--------------------------------------\n")
    for cluster in c:
        stringC = ""
        for vertex in cluster:
            stringC += g.vs[vertex]["idx"] + " "
        file.write(stringC + "\n")
    '''
    '''
    Q=g.modularity(c)
    vertexIDList =[]
    for vertexVal in c[0]:
        vertexIDList.append(g.vs[vertexVal]["idx"])
    print("List of vertex id's in largest cluster: ")
    print(vertexIDList)
    '''
    
    # summary(c)
    # print("Number of clusters using infomap " + str(len(c)))
    # giant = c.giant()
    # print("Number of vertices in largest cluster:" + str(len(giant.vs)))
    # print("\t" + str(len(giant.vs)/len(g.vs)*100) + "% of all the verticies in the graph.")
    '''
    # c = g.clusters()
    i = g.community_infomap()
    print(i)
    colors = ["#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00"]
    g.vs['color'] = [None]
    for clid, cluster in enumerate(i):
        for member in cluster:
            g.vs[member]['color'] = colors[clid]
    g.vs['frame_width'] = 0
    plot(g)
    '''
    # NOTE: cl = g.community_fastgreedy().as_clustering() IS POSSIBLE??
    # c = g.clusters()
    # print("Number of clusters using basic clustering: " + str(len(c)))
    
    # cgraph = c.cluster_graph()
    # plot(cgraph)
    
    # Can access a subgraph here via index
    # sub = c.subgraph(0)
    # plot(sub)
    
    # giant = c.giant()
    # print("Number of vertices in largest cluster:" + len(giant.vs))
    # print("\t" + str(len(giant.vs)/len(g.vs)*100) + "% of all the verticies in the graph.")
    # summary(giant)
    # for vertex in giant.vs:
        # print(vertex)
    #plot(giant, vertex_color=["red" if type == 0 else "blue" for type in g.vs["type"]], vertex_label=[name for name in giant.vs["idx"]], edge_width = [weight for weight in giant.es["weight"]], edge_label = [weight for weight in giant.es["weight"]])

    # change to elif later!!

def generateWordCloud():
    for i in range(1,7):
        file = open('select_six_post_content_{}.txt'.format(i), 'r', encoding="utf-8")
        stopWordsFile = open('stopwords.txt', 'r')
        
        fig = plt.figure(figsize=(20, 10))
        ax  = fig.add_subplot('111')
        
        wcloud = WordCloud(background_color="white", mode = "RGB", width=2000, height = 1000, stopwords = stopWordsFile.read().split('\n')).generate(file.read())
        plt.title("wordcloud_{}".format(i))
        plt.imshow(wcloud)
        plt.axis("off")
        fig.tight_layout()
        fig.savefig('select_six_wordplot_{}.png'.format(i))
        
def generateWordCloud2():
    DBname = "MichalisPrj"
    pword = "1"
    tableName = "tbl_hackthissite_post"
    con = psycopg2.connect(database=DBname, user = "postgres", password=pword) #connect to postgres
    curs = con.cursor()
    
    for num in range(1,7):
        c1 = pickle.load(open("graph-and-edges\select_six_{}.pickle".format(num), "rb"))
        c1_degreeList = c1.degree()
        total = np.sum(c1_degreeList)
        degreeList = []
        
        for i, degree in enumerate(c1_degreeList):
            percentage = (degree/total)*100
            if c1.vs[i]["type"] == 1:
                degreeList.append((percentage, c1.vs[i]["idx"]))
                
        degreeList.sort(key=operator.itemgetter(0), reverse=True)
        
        plotString = ""
        
        #1 has 6 significant threads
        #2 has 3 significant threads
        #3 has 5 significant threads EXCLUDING the first one (outlier)
        #4 has 6 significant threads
        #5 has 7 significant threads
        #6 has 6 significant threads
        sig_num_threads_dict = {
            1: [0,6],
            2: [0,3],
            3: [1,6], #1 for the outlier, six to push everything back by 1
            4: [0,6],
            5: [0,7],
            6: [0,6],
        }
        #fix this later to actually calculate the significant number of threads
        
        for strng in degreeList[sig_num_threads_dict[num][0]:sig_num_threads_dict[num][1]]:
            tid = strng[1][4:]
            ExecuteStatement = "SELECT post_content FROM " + tableName + " WHERE tid = '{}'".format(tid)
            curs.execute(ExecuteStatement)
            postList = curs.fetchall()
            for post in postList:
                cleanStr = clean(str(post))
                cleanStr = cleanStr[3:-4]
                plotString += cleanStr + "\n"
            
        
        stopWordsFile = open('stopwords.txt', 'r')
        
        fig = plt.figure(figsize=(20, 10))
        ax  = fig.add_subplot('111')
        
        wcloud = WordCloud(background_color="white", mode = "RGB", width=2000, height = 1000, stopwords = stopWordsFile.read().split('\n')).generate(plotString)
        sorted_wcloudWords = sorted(wcloud.words_.items(), key=operator.itemgetter(1), reverse = True)
        file = open('wordCloud_{}_Topics.txt'.format(num), 'w')
        for word in sorted_wcloudWords:
            file.write(word[0] + "\n")
        plt.title("wordcloud_{}".format(num))
        plt.imshow(wcloud)
        plt.axis("off")
        fig.tight_layout()
        fig.savefig('significant_threads_wordplot_{}.png'.format(num))
    
def buildCDF(list, filename):
    clusterSizes = list    
    for i, element in enumerate(clusterSizes):
        clusterSizes[i] = int(element)
    clusterSizes = sorted(clusterSizes)
    # print(clusterSizes)
    
    cnt = Counter()
    for size in clusterSizes:
        cnt[size] += 1
        
    sizeCounts = []
    for element in sorted(cnt):
        sizeCounts.append(cnt[element])
    
    sizeCounts = np.array(sizeCounts)
    cumSizeCounts = sizeCounts.cumsum()
    
    maxVal = max(cumSizeCounts)
    y=[]
    for element in cumSizeCounts:
        y.append(element/maxVal)

    
    file = open('cumulative_distribution_plotlist.txt', 'w')
    file.write("Plot points:\n")
    file.write("x --> y  \n")
    file.write("-----------\n")
    printString = ""
    for i, element in enumerate(sorted(cnt)):
        printString += (str(element) + " --> " + str(y[i]) + "\n")
    file.write(printString)

    '''
    plt.plot(sorted(cnt),y)
    plt.ylabel('percentage')
    plt.xlabel('degree')
    plt.show()
    '''
    
    fig = plt.figure(figsize=(8, 6))        
    ax = fig.add_subplot(111)
    
    ax.plot(sorted(cnt), y)
    ax.set_xlabel('log(degree)')
    ax.set_ylabel('percentage')
    ax.set_xscale('log')
    
    fig.tight_layout()
    fig.savefig(filename)
        
    
    
def distributionFunc(g, func="CDF-Degree", filename="", filenameSeperator=",", saveFileName="cdf_default.png"):
    if func == "CDF-Degree":
        degreeListUsers = sorted(g.degree())
        print("Vertex with largest degree: " + str(g.vs.select(_degree = g.maxdegree())["idx"]))
        buildCDF(degreeListUsers, filename=saveFileName)
        
    elif func == "CDF-File":
        file = open(filename, 'r')
        clusterSizes = file.read().split(filenameSeperator)
        buildCDF(clusterSizes, filename=saveFileName)
        
    elif func == "PDF-degree":
        degreeListUsers = np.array(g.degree())
        print("ID of Vertex with largest degree: " + str(g.vs.select(_degree = g.maxdegree())["idx"]))
        
        totalValue = sum(degreeListUsers)
        print("Total Degree value: " + str(totalValue))
        x= []
        y = []
        
        file = open('degree_of_users_list.txt', 'w')
        file.write("List of all degress of users:\n")
        file.write("---------------------------\n")
        file.write(str(degreeListUsers))
        
        intX = 1
        for degree in degreeListUsers:
            x.append(intX)
            intX += 1
            y.append((degree/totalValue) * 100)
         
        print(y)
        plt.plot(x, y)
        plt.ylabel('probability')
        plt.xlabel('users')  
        plt.show()
    
    else:
        print("ERROR! Syntax: Neither CDF-\" \" or PDF-\" \" was chosen.")
        print("In the parameter of the function please specify either \'func=\"CDF-(type)\"\' or \'func=\"PDF-(type)\"\'")
        print("--- No output ---")
    
def clean(postContent):
    postContent = re.sub(r'(\\t)*(\\n)*','',postContent) #removes all \n and \t
    soup = BeautifulSoup(postContent, "html.parser")
    postContent = soup.get_text(separator=" ").replace("<br>", " ").lower() #lowercase it all to make searching easier
#     print(postContent.encode("utf-8")) #for testing purposes
    return postContent
    
    
if __name__ == "__main__":
    start_time = time.time()
    # g = buildGraph(save=True)
    # plot(g, vertex_color=[color for color in g.vs["color"]],  edge_width = [weight for weight in g.es["weight"]])
    # clusters = g.clusters()
    # algoTest(clusters.giant(), func="fastGreedy")
    # algoTest(g=None, func="getPostContentFromEdgeList")
    # algoTest(g=None, func="vertexDegreeDistribuion")
    algoTest(g=None, func="printSigThreads")
    # generateWordCloud2()
    
    # distributionFunc(g, func="CDF-File", filename="fastGreedy_cluster_lenghts.txt", filenameSeperator='\n')
    # distributionFunc(g, func="CDF-Degree")
    
    # g = pickle.load( open( "save.p", "rb" ) )
    # summary(g)


    print("done: --- %s seconds ---" % (time.time() - start_time))