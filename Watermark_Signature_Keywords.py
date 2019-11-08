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
import shutil

## REQUIREMENTS : flask, nltk, PyPDF2, textract, panda, sklearn

# ********* Note: This script contains three section *******

## 1. Keywords extraction as /keywords === INPUT: JSON data >> { "title" : "value", "abstract" : "abstract_value" }
## 2. Digital watermarking as /watermark === INPUT: form-data >> pdf_file and author_name
## 3. Book Recommendation as /recommendation 
app = Flask(__name__)

@app.route('/keywords',methods=['POST'])
def extract():
	data = request.get_json()
	nltk.data.path.append('./nltk_data/')
	title = data['title']
	abstract = data['abstract']
	
	book_title = title.lower()
	
	book_stract = abstract.lower()
	
	book_stract = re.sub('[\-/]',' ',book_stract)

	input_string = nltk.word_tokenize(book_stract)

	tagged = nltk.pos_tag(input_string)
	print(tagged)

	output = []
	for word,tag in enumerate(tagged):
		if tag[1] == "NN" or tag[1] == "NNS" or  tag[1] = "NNP" or tag[1] == "NNPS" or tag[1] == "JJ" or tag[1] == "JJR" or tag[1] == "JJS":
			output.append(tag[0])

	return make_response(jsonify({
	"title" : book_title,
	"abstract" : output
	}),200)



################### WATERMARKING ##############################
############ THIS SECTION IS WATERMARK SECTION##############


DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/watermarked/'
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/storage/'
CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

@app.route('/watermark', methods=['POST'])

def index():
	data = request.get_json()
	author = data['authorname']
	filepath = data['pdfpath']
	fullpath = UPLOAD_FOLDER+filepath
	filename = re.sub('.*/','',filepath)
	if os.path.exists(CURRENT_FOLDER+filename):
		os.remove(CURRENT_FOLDER+filename)
		shutil.copy(fullpath,filename)
	else:
		shutil.copy(fullpath,filename)
	process_file(filename,author)
	os.remove(CURRENT_FOLDER+filename)
	return make_response(jsonify({
	"watermarked" : filename
	}),200)
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

CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))+'/'
@app.route('/recommendation',methods=['POST'])
def recommendation():
    bk = request.get_json()
    bk_id = bk['book_id']
    bk_title = bk['title']
    path = bk['json_file']
    path = CURRENT_FOLDER + path
    num = bk_id
#    num = int(num.replace("[","").replace("]","")) ## chosen id from web
    print("chosen id",num)
#    path = path.translate(str.maketrans({'[':'',']':'','\'':''}))
 #   print("path",path) ## path for keyword extracted json

    with open(path) as books:
        df = pd.read_json(books) ## books is json string
    #print(df)
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
    
    # print(check)
    #input the index of the book and get top 10 book recommendation
    row_no = str(check[check['book_id'] == num].index.values)
    row_no = int(row_no.replace("[","").replace("]",""))
    #print("THIS IS ROW NO")
    #print(row_no)
 #   row_no = int(row_no.replace("[","").replace("]","")) ## chosen id from web
    # print("Index values for recommendation",row_no)
    recom = recommend(row_no, cosine_similarity,indices,df) ## need to edit, chosen id from web instead of 1

    book_id= []
    #for book title
    book_title = []
    for book in recom:
        book_title.append(book)
    #print("title",book_title)
    check= check.set_index('title')
    for i in range(len(book_title)):
        book_id.append(int(check.loc[book_title[i],'book_id'])) #for book Id
    #print("book_id",book_id)

    #for bookId and Title json
    output_json=[]
    #inside = {}
    for i in range(len(book_title)):
        ##inside["book_id"] = book_id[i]
        ##inside["book_title"] = book_title[i]
        output_json.append({"book_id": book_id[i],"book_title":book_title[i]})
    #print("json",output_json)
    return json.dumps(output_json)
    # return "hello"
def recommend(index, method,indices,df):

    id = indices[index]
    #print("id",id)
    # Get the pairwise similarity scores of all books compared that book,
    # sorting them and getting top 5
    similarity_scores = list(enumerate(method[id]))
    #print("sim",df)
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    similarity_scores = similarity_scores[1:6]
      
        #Get the books index
    books_index = [i[0] for i in similarity_scores]
        
        #Return the top 10 most similar books using integar-location based indexing (iloc)
    ##print("result",df['title'].iloc[books_index])
    return df['title'].iloc[books_index]


if __name__ == '__main__':
   app.run(host = "127.0.0.1",port = "5000",debug=True)
