from flask import Flask, jsonify, make_response, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
import nltk
import PyPDF2
import textract
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re,io,sys,random,os,datetime
from fractions import gcd
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd

## REQUIREMENTS : flask, nltk, PyPDF2, textract, panda, sklearn

# ********* Note: This script contains three section *******

## 1. Keywords extraction as /keywords === INPUT: JSON data >> { "title" : "value", "abstract" : "abstract_value" }
## 2. Digital watermarking as /watermark === INPUT: form-data >> pdf_file and author_name
## 3. Book Recommendation as /recommendation 
app = Flask(__name__)

output = []

@app.route('/keywords',methods=['POST'])
def extract():
	data = request.get_json()
	nltk.data.path.append('./nltk_data/')
	title = data['title']
	abstract = data['abstract']
	
	book_title = title.lower()
	
	book_stract = abstract.lower()

	input_string = nltk.word_tokenize(book_stract)

	tagged = nltk.pos_tag(input_string)

	for word,tag in enumerate(tagged):
		if tag[1] == "NN" or tag[1] == "NNS" or tag[1] == "NNP" or tag[1] == "NNPS" or tag[1] == "JJ" or tag[1] == "JJR" or tag[1] == "JJS":
			output.append(tag[0])

	return make_response(jsonify({
	"title" : book_title,
	"abstract" : output
	}),200)


################### WATERMARKING ##############################
############ THIS SECTION IS WATERMARK SECTION##############

DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/downloads/'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
filename = ""
for filename in os.listdir(UPLOAD_FOLDER):
    filename = filename
   
@app.route('/watermark', methods=['POST'])

def index():
	data = request.get_json()
	author = data['authorname']
	process_file(filename,author)
	return redirect(url_for('uploaded_file', filename=filename))

def process_file(path, author):
	watermark(path,author)

def watermark(path,author):
	pdfFileObj = open(path, 'rb') 
	pdfReader = PyPDF2.PdfFileReader(pdfFileObj) 
	pdfWriter = PdfFileWriter()
	f = author
	packet = io.BytesIO()
	can = canvas.Canvas(packet, pagesize=A4)
	width, height = A4
	time = datetime.datetime.today()
	date = time.strftime("%h-%d-%Y %H:%M:%S")
	can.setFont("Times-Roman", 10)
	can.rotate(90)
	can.drawString(0.5*inch, -inch, '''Created by %s at Date: %s''' % ( f, date))
	can.save()
	mywatermark = PdfFileReader(packet)
  
	for page_number in range(pdfReader.getNumPages()):
		wmpageObj = add_watermark(mywatermark, pdfReader.getPage(page_number)) 
		pdfWriter.addPage(wmpageObj) 
	output_stream = open(app.config['DOWNLOAD_FOLDER'] + path, 'wb')
	pdfWriter.write(output_stream)
  
def add_watermark(wmFile, pageObj): 
	pageObj.mergePage(wmFile.getPage(0)) 
	return pageObj

@app.route('/uploads/<filename>')

def uploaded_file(filename):
	return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)


######## BOOK RECOMMENDATION ###########

@app.route('/recommendation',methods=['POST'])
def recommendation():
    bk = request.get_json()

    # ###### Example  #################
    # jsons = """{"book_id":2,
    # "book_title":"Hello",
    # "abstract":"fkjdkfaksd dkfja ldsjf",
    # "json_file": "keyword.json"}"""
    # books = json.loads(jsons) ## jsonstring
    # # books= json.dumps(books) # convert list to json string
    # bk = pd.DataFrame(books,index=[0]) ## books is json string
    # print(bk)
    # #################################

    bk_id = bk['book_id']
    path = bk['json_file']
    print(bk_id.values,path.values)
    num = str(bk_id.values)
    path = str(path.values)
    num = int(num.replace("[","").replace("]","")) ## chosen id from web
    print("chosen id",num)
    path = path.translate(str.maketrans({'[':'',']':'','\'':''}))
    print("path",path) ## path for keyword extracted json

    with open(path) as books:
        df = pd.read_json(books) ## books is json string
    # print(df)
    check = df[['book_id','title']]
    df.set_index('book_id',inplace=True)
    # initializing the new column
    df['final_text'] = ""
    # get final text for recommendation
    for index, row in df.iterrows():
        title=row['title']
        abstract=row['abstract']
        tokens = title.split()
        # remove punctuation from each token
        table = str.maketrans('', '', string.punctuation)
        tokens = [w.translate(table) for w in tokens]
        # remove remaining tokens that are not alphabetic
        tokens = [word for word in tokens if word.isalpha()]
        # filter out stop words
        stop_words = set(stopwords.words('english'))
        tokens = [w for w in tokens if not w.lower() in stop_words]
        title =' '.join(map(str,tokens))
        abstract =' '.join(map(str,abstract))
        text = title+" "+abstract
        row['final_text'] = text
    # dropping the abstract column
    df.drop(columns = ['abstract'], inplace = True)
    # print(df)

    vectorizer = TfidfVectorizer(analyzer='word')
    #build final-text to tfidf matrix
    tfidf_matrix = vectorizer.fit_transform(df['final_text'])
    # tfidf_feature_name = vectorizer.get_feature_names()

    # comping cosine similarity matrix using linear_kernal of sklearn
    cosine_similarity = linear_kernel(tfidf_matrix, tfidf_matrix)

    df = df.reset_index(drop=True)
    indices = pd.Series(df['title'].index)
    #Function to get the most similar books
    def recommend(index, method):
        id = indices[index]
        # Get the pairwise similarity scores of all books compared that book,
        # sorting them and getting top 5
        similarity_scores = list(enumerate(method[id]))
        similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
        similarity_scores = similarity_scores[1:6]
        
        #Get the books index
        books_index = [i[0] for i in similarity_scores]
        
        #Return the top 10 most similar books using integar-location based indexing (iloc)
        return df['title'].iloc[books_index]

    # print(check)
    #input the index of the book and get top 10 book recommendation
    row_no = str(check[check['book_id'] == num].index.values)
    row_no = int(row_no.replace("[","").replace("]","")) ## chosen id from web
    # print("Index values for recommendation",row_no)
    recom = recommend(row_no, cosine_similarity) ## need to edit, chosen id from web instead of 1

    book_id= []
    #for book title
    book_title = []
    for book in recom:
        book_title.append(book)
    check= check.set_index('title')
    for i in range(len(book_title)):
        book_id.append(int(check.loc[book_title[i],'book_id'])) #for book Id

    #for bookId and Title json
    output_json=[]
    for i in range(len(book_title)):
        output_json.append({"book_id": book_id[i],"book_title":book_title[i]})
    print(output_json)
    return make_response(jsonify(output_json),200)
    # return "hello"


if __name__ == '__main__':
   app.run(host = "127.0.0.1",port = "5000",debug=True)
