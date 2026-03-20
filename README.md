to run urbanbyte on local host, follow these steps
1. make sure to unzip the zip file.
2. first copy the address of the frontend folder, open the cmd and type cd <frontend address>
3. then type this command python -m http.server 5500
4. then open a new cmd window, don't close the existing one, but open a sepreate window
5. copy the address of the backend folder, and type this in new cmd window, cd <backend address>
6. now type the following commands -
 python -m venv venv
venv\Scripts\activate        # Windows
or
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python app.py
7. now open browser and type this http://localhost:5500
8. your website is now functioning





Thank You