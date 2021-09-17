import os
import argparse
import re
import json
from datetime import datetime, timedelta
from datetime import date
from io import StringIO
import urllib.request
from urllib.error import HTTPError

import tensorflow as tf
import numpy as np
import pandas as pd
import cv2
import pytesseract
import pyarrow.feather as feather
import matplotlib.pyplot as plt
from PIL import Image
import PIL


def CovidScraper(dates,datastring,url_base,flag,config,output):
  for i in dates:
    try:
      req = urllib.request.urlopen(url_base+i+".jpg")
    except HTTPError as err:
      if err.code == 404:
        continue
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img = cv2.imdecode(arr, -1)
    if(flag is not None and flag==True):
      if not os.path.exists(output+"/covid_19_images"):
        os.makedirs(output+"/covid_19_images")
      im1 = Image.fromarray(img) 
      im1 = im1.save(output+"/covid_19_images/"+i+".jpg")
        
    infected = img[286:474, 792:1146]
    dead = img[286:478, 1169:1458]

    scale_percent = 5 # percent of original size
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    
    # resize image
    infected = cv2.resize(infected, dim)
    dead = cv2.resize(dead,dim)
    #Used [:-2] because image_to_string outputs newline
    datastring+=i+","+pytesseract.image_to_string(infected, config=config)[:-2]+','+pytesseract.image_to_string(dead, config=config)[:-2]+"\n"
  return datastring

def main():
  parser = argparse.ArgumentParser(description='Scrapper for Covid19.gov.gr.Generate csv for any specified dates')
  parser.add_argument('--start_date', '-s', type=str, default="2020-12-03",
                      help='Starting date(Y-m-d) for scraping')
  parser.add_argument('--end_date', '-e', type=str, default=str(date.today()),
                      help='Ending date(Y-m-d) for scraping')
  parser.add_argument('--output', '-o', type=str, default=str(os.getcwd())+'/output/',
                      help='Directory to output the data')
  parser.add_argument('--csv_feather_json', '-cfj', type=str, default="csv",choices=['csv','feather','json'],
                      help='File Format of Data')
  parser.add_argument('--save_imgs', type=bool, default=True,choices=[True,False],
                      help='Save scraped images inside a folder')
  parser.add_argument('--give_csv', type=str,
                      help='Give output.csv and fetch all new days')
  parser.add_argument('--step', '-i',type=int, default=1,
                      help='Give step of days')
  args = parser.parse_args()
  r = re.compile('^(19|20)\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])$')
  if(args.give_csv is not None):
    msft = pd.read_csv(args.give_csv,sep=",")
    if(r.match(msft.tail(1).values[0][0]) is None):
      print("Provided csv has false data.")
      return -1
  if(r.match(args.start_date) is None):
    print(args.start_date+" is not a valid date.")
    return -1
  elif(r.match(args.end_date) is None):
    print(args.end_date+" is not a valid date.")
    return -1
  elif(args.start_date>args.end_date):
    print("start_date cant be bigger than end_date")
    return -1
  elif(args.start_date>str(date.today())or args.end_date>str(date.today())):
    print("start_date and/or end_date must not be after : "+str(date.today()))
    return -1
  elif(args.step<=0):
    raise argparse.ArgumentTypeError("Minimum step is 1")
  else:
    #Url base for image scrapping
    url_base="https://covid19.gov.gr/wp-content/uploads/stat_date/"

    #Begining of multiline in order to create the csv"
    datastring=""" Date , Infections , Deaths \n"""

    #Generate a data frame with all dates in the given period[start_date-end_date].
    dates = pd.date_range(start=args.start_date,end=args.end_date,freq=str(args.step*1440)+"min")
    
    #Keep only the Year-Month-Day
    dates = dates.strftime('%Y-%m-%d')
    if(args.give_csv is not None):
      msft = pd.read_csv(args.give_csv,sep=",")
      start_date = datetime.strptime(msft.tail(1).values[0][0], "%Y-%m-%d")
      start_date = start_date + timedelta(days=1)
      dates = pd.date_range(start=start_date,end=date.today(),freq=str(args.step*1440)+"min")
      dates = dates.strftime('%Y-%m-%d')

    #Command line args for tesseract
    custom_config = r'-c tessedit_char_whitelist=1234567890 -c tessedit_char_blacklist=/] --psm 6'

    if(args.save_imgs):
      data = StringIO(CovidScraper(dates,datastring,url_base,args.save_imgs,custom_config,args.output))
    else:
      data = StringIO(CovidScraper(dates,datastring,url_base,None,custom_config,args.output))

    df = pd.read_csv(data, sep=",")
    if not os.path.exists(args.output):
      os.makedirs(args.output)
    if(args.give_csv is not None):
      df = pd.concat([df, msft],ignore_index=True)
      df = df.sort_values(by=" Date ")
    if (args.csv_feather_json.lower()=="csv"):
      df.to_csv(args.output+"/output.csv",index=False)
    elif (args.csv_feather_json.lower()=="feather"):
      feather.write_feather(df, args.output+"/output.feather")
    elif (args.csv_feather_json.lower()=='json'):
      with open(args.output+"output.json", 'w', encoding='utf-8') as f:
        json.dump(df.to_json(orient='records')[1:-1].replace('},{', '} {'), f, ensure_ascii=False, indent=4)
    else:
      if len(os.listdir(args.output)) == 0:
        os.rmdir(args.output)
      return -1
    
if __name__ == "__main__":
  main()
