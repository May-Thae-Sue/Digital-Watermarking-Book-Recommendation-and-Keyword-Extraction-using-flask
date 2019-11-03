
# Digital-Watermarking-Signature-and-Keyword-Extraction-using-flask

## REQUIREMENTS : flask, nltk, PyPDF2, panda

 ********* Note: This script contains five section *******

 1. Keywords extraction section as /keywords === INPUT: JSON data >> { "title" : "value", "abstract" : "abstract_value" }
 2. Digital watermarking section as /watermark === INPUT: form-data >> pdf_file and author_name
 3. Recommendation System as /recommendation 

To run this script, **Postman** App can be used or Terminal can also be use

Firstly, 
type : python3 Watermark_Signature_Keywords.py

And then: open a new terminal,

For keyword extraction,
**curl POST -H "Content-Type: application/json" -d '{"title":"Book_Title","abstract":"Book_Abstract"} http://127.0.0.1:5000/keywords**

For Digital watermarking,
**curl  -F file=@Chapter_2.pdf -F name="author_name" http://127.0.0.1:5000/watermark**

