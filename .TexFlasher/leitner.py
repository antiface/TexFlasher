#!/usr/bin/python

#     This file is part of TexFlasher.
#     Copyright (c) 2012:
#          Can Oezmen
#          Axel Pfeiffer
#
#     TexFlasher is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     TexFlasher is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with TexFlasher  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import sys
import re
import commands
import xml.dom.minidom as xml
from operator import itemgetter
from time import gmtime, strftime, strptime, mktime, ctime, localtime
from datetime import datetime, timedelta
from Tkinter import *
from math import *
import tkFont
import tkMessageBox
import Image, ImageTk
import tkFileDialog
from difflib import get_close_matches
import itertools, collections
import glob


######################################################################## leitner_db management ###########################################################


def load_leitner_db(leitner_dir,user):
	if not os.path.isdir(leitner_dir+"/Karteikarten"):
		print "No directory named Karteikarten found in "+leitner_dir
		sys.exit()
	#load old flashcards
	if os.path.isfile(leitner_dir+"/Users/"+user+".xml"):
		try:
			old_ldb= xml.parse(leitner_dir+"/Users/"+user+".xml")
		except:
			pass
	#create new flashcard xml
	flashcards_dir=os.listdir(leitner_dir+"/Karteikarten")
	doc=xml.Document()
	ldb = doc.createElement('ldb')
	for flashcard_file in flashcards_dir:
		if flashcard_file.split(".")[-1]=="pdf":
			flashcard_name=flashcard_file.split(".")[0]
			#mod_sec=os.stat(leitner_dir+"/Karteikarten/"+flashcard_file).st_mtime
			#mod_date=datetime(*(strptime(strftime("%Y-%m-%d %H:%M:%S",localtime(mod_sec)), "%Y-%m-%d %H:%M:%S")[0:6]))

			try: 
				flashcard_element=old_ldb.getElementsByTagName(flashcard_name)[0] #raises if old_ldb does not exist or not found
				ldb.appendChild(flashcard_element)
			#		lastReviewed_date=datetime(*(strptime(flashcard_element.getAttribute('lastReviewed'), "%Y-%m-%d %H:%M:%S")[0:6])) #this raises if not reviewed yet	#		if mod_date>lastReviewed_date: 
			#			changed.append(flashcard_element.tagName)

			except:
				#create new flashcard node
				flashcard_element=doc.createElement(flashcard_name)
				ldb.appendChild(flashcard_element)
				flashcard_element.setAttribute('lastReviewed', "")
				flashcard_element.setAttribute('level',"0")
				flashcard_element.setAttribute('levelHistory',"0_("+strftime("%Y-%m-%d %H:%M:%S", localtime())+")")
				flashcard_element.setAttribute('created',strftime("%Y-%m-%d %H:%M:%S", localtime()))
	xml_file = open(leitner_dir+"/Users/"+user+".xml", "w")
	ldb.writexml(xml_file)
	#pretty_xml = ldb.toprettyxml()
	#xml_file.writelines(pretty_xml)
	xml_file.close()
	return ldb


def futureCardNumber( database, offset, offset2, maxLevel ):
	LEVELS=[]
	
	for i in range(maxLevel+1):
		LEVELS.append(0)
	number=0
	seconds_in_a_day = 60 * 60 * 24
	for elem in database.childNodes:
		name=elem.tagName
		lastReviewed=elem.getAttribute('lastReviewed')
		if lastReviewed!="":
			lastReviewed_time=datetime(*(strptime(lastReviewed, "%Y-%m-%d %H:%M:%S")[0:6]))
		        level=int(elem.getAttribute('level'))
			dt_1 = lastReviewed_time + timedelta(days=(level - (offset + offset2)))		
			dt_2 = lastReviewed_time + timedelta(days=(level - offset))		
		
			if (datetime.now() + timedelta(hours=int(24 - datetime.now().hour + 3)) < dt_1):
				if datetime.now() + timedelta(hours=int(24 - datetime.now().hour + 3)) >= dt_2:
					number += 1
					LEVELS[level] +=1
		else:
			if offset == 0:
				number += 1	
				LEVELS[int(elem.getAttribute('level'))] += 1
	return number, list(LEVELS)


def load_agenda(ldb,dir,now=datetime.now()):
	local_agenda={}
	flashcards=ldb.childNodes
	seconds_in_a_day = 60 * 60 * 24
	new_fc={}
	try:
		order = xml.parse(dir+"/Karteikarten/order.xml")
		for elem in flashcards:
			name=elem.tagName
			lastReviewed=elem.getAttribute('lastReviewed')
			if lastReviewed=="":
				place=int(order.getElementsByTagName(elem.tagName)[0].getAttribute("position"))
				new_fc[elem.tagName]=place
			else:
				lastReviewed_time=datetime(*(strptime(lastReviewed, "%Y-%m-%d %H:%M:%S")[0:6]))
				level=elem.getAttribute('level')
				dt = lastReviewed_time + timedelta(days=int(level))		
				if datetime.now() + timedelta(hours=int(24 - datetime.now().hour + 3))>=dt:
					diff=now-dt
					local_agenda[elem.tagName]=diff.days * seconds_in_a_day + diff.seconds
	except:
		pass
	sorted_agenda = sorted(local_agenda.iteritems(), key=itemgetter(1))
	sorted_agenda.reverse()
	sorted_new=sorted(new_fc.iteritems(), key=itemgetter(1))	
	return sorted_agenda+sorted_new,len(sorted_new)


def update_flashcard(fc_tag,ldb,selected_dir,attr_name,attr_value,lastReviewed=strftime("%Y-%m-%d %H:%M:%S", localtime()),ask=False):
	update=True
	flashcard_element=ldb.getElementsByTagName(fc_tag)[0]
	try:
		if ask and attr_name=="Level":
			update=False
			if tkMessageBox.askyesno("Reset", "Do you really want to reset the learning progress for this flashcard?"):
				update=True				
		if update==True and attr_name=="Level":
			flashcard_element.setAttribute('lastReviewed',lastReviewed)
			flashcard_element.setAttribute('level', str(attr_value))
			flashcard_element.setAttribute('levelHistory', flashcard_element.getAttribute('levelHistory')+str(attr_value)+"_("+strftime("%Y-%m-%d %H:%M:%S", localtime())+")" )
		elif update==True:
			flashcard_element.setAttribute(attr_name, str(attr_value))
	
		if update==True:
			xml_file = open(selected_dir+"/Users/"+user+".xml", "w")
			ldb.writexml(xml_file)
			xml_file.close()
	except:
		print "Error while updating "+fc_tag+" attribute "+attr_name+" to "+str(attr_value)

################################################ Statistics ################################################################


def statistics_nextWeek(ldir):
		checkForUpdate()
		database = load_leitner_db(ldir, user)
		DAYS=[]
		LEVELS=[]
		DATASET=[]

		flashcards = database.childNodes
		maxLevel = -1
		cards = 0.0 
		for card in flashcards:
			maxLevel = max( maxLevel, int( card.getAttribute('level') ) )
			cards += 1.0
		
		for i in range(maxLevel+1):
			LEVELS.append(0)
		
			
		for day in range(7):
			number, listOfLevels = futureCardNumber( database, day , -1 , maxLevel)
			DAYS.append( number )
			DATASET.append( [ number, list(listOfLevels)  ] )
		
		#print DATASET
		# fix for day=0
		number1, listOfLevels1 = futureCardNumber( database, 0, -1000000, maxLevel )
		DAYS[0] = number1
		DATASET[0] = [number1, list(listOfLevels1)]
		
		# TODO look into this once more
		for card in flashcards:
			LEVELS[int( card.getAttribute('level'))] += 1.0/cards
		
		
		graph_points(DATASET, LEVELS, cards ,ldir)
		
		

def dayToday():
    now = datetime.now()
    
    d = now.day
    m = now.month
    y = now.year
    
    if m < 3:
        z = y-1
    else:
        z = y
    dayofweek = ( 23*m//9 + d + 4 + y + z//4 - z//100 + z//400 )
    if m >= 3:
        dayofweek -= 2
    dayofweek = dayofweek%7
    return dayofweek-1
		
#def getColor( i, maxLevel ):
	#if i > 3:
		#if( (maxLevel - 5) <= 0 ):
			#n = 1
		#else:
			#n = log(maxLevel - 5)
		#i = int(round( pow(float(i), n ) + 2, 0))
	#COLORS = "yellow", "orange red",  "darkgreen", "indian red", "light sea green", "orange", "RoyalBlue1",  "lightblue"
	#if i == 0:
		#return COLORS[0]
	#else:
		#pos = i
		#while( pos+1> len(COLORS)):
			#pos -= len(COLORS)
		#return COLORS[pos]

#def getColor( i, maxLevel ):
	#COLORS = "yellow", "orange red",  "darkgreen", "indian red", "light sea green", "orange", "RoyalBlue1",  "lightblue"
	#if i <= 3:
		#return COLORS[i]
	#elif i <= 5:
		#return COLORS[4]
	#elif i <= 9:
		#return COLORS[5]
	#else:
		#return COLORS[6]
		
def getColor( i, maxLevel ):
	delim=2
	dl =int( round( (maxLevel-delim)/3.0, 0 ) )
	COLORS = "yellow", "red", "orange red", "#00CC00","#009900", "#006600"
	if i <= delim:
		return COLORS[i], dl
	else:
		if( i-delim <= dl ):
			return COLORS[delim+1], dl
		elif( i-delim <= 2*dl):
			return COLORS[delim+2], dl
		else:
			return COLORS[delim+3], dl
		
def graph_points(dataSetC, dataSetB, numCards,dir):
    clear_window()
    top.title(version+" - Statistics")


    menu_button=create_image_button(top,"./.TexFlasher/menu.png",40,40)
    menu_button.configure(text="Menu",command=lambda:menu())
    menu_button.grid(row=0,columnspan=7)
    Stats=Frame(top,border=10)
    Stats.grid(row=2,column=0)
    
    DAYS =[ 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun' ]
    tday=dayToday()   
           
    global c
    c = Canvas(Stats, width=int(float(WIDTH)*0.4999), height=int(WIDTH*0.6))  
    c.grid(row=1 , column=0, sticky=W+E)
    
    ymax=1
    for i in range(len(dataSetC)):
			ymax = max(ymax, dataSetC[i][0])

    D1= 50.0
    D2=0.6*(WIDTH*0.6)
    zero= D1, float(HEIGHT)*0.65
    

    valMax=5
    stepsize = 5
    if( ymax >= 100 ):
			stepsize = 25
    elif (ymax >= 40):
			stepsize = 10
					
    if(ymax%stepsize==0):
				valMax=ymax
    else:
			for i in range(1,stepsize):
				if (ymax+i) % stepsize == 0:
					valMax = (ymax+i)
					break
			
    c.create_rectangle(zero[0], 0.25*zero[1] , int(float(WIDTH)*0.4999), zero[1],width=0,fill="grey85")
			
			
    for i in range(1, 1000):
			c.create_line(zero[0], zero[1] - float(i*stepsize*D2)/float(valMax), int(float(WIDTH)*0.4999), zero[1]-float(i*stepsize*D2)/float(valMax), fill="grey50")
			c.create_line(zero[0]-0.1*D1, zero[1] - float(i*stepsize*D2)/float(valMax), zero[0]+0.1*D1, zero[1]-float(i*stepsize*D2)/float(valMax))
			c.create_text(zero[0]-0.1*D1, zero[1] - float(i*stepsize*D2)/float(valMax), anchor=E, text=str(i*stepsize))
			if (ymax <= i*stepsize):
				break
	
    assert(valMax >= 0)

    y_stretch = 0.6*(WIDTH*0.6)/valMax
    y_gap = 20
    x_stretch = 10
    x_width = 37
    n = len(dataSetC)

    for x in range(len(dataSetC)):
        x0 = x * x_stretch + x * x_width + zero[0] +x_stretch
        y0 = zero[1] - (dataSetC[x][0] * y_stretch )
        x1 = x * x_stretch + x * x_width + x_width +zero[0] +x_stretch
        y1 = zero[1]
        if y1==y0:
					y0 -= 1
					
        c.create_rectangle(x0, y0, x1, y1, fill="Red", width=2)
        lastYpos = y0
        for i in range(len(dataSetC[x][1])):
					color, foo=getColor(i, len(dataSetB))
					c.create_rectangle(x0+1, lastYpos +dataSetC[x][1][i]*y_stretch  , x1-1, lastYpos, fill=color, width=0)
					lastYpos += dataSetC[x][1][i]*y_stretch
        c.create_line(x0, y0, x1, y0, width=2 )
					
        if( dataSetC[x][0] > 0 ):
					if( y1-y0 > 20 ):
						c.create_text(0.5*(x0+x1), y0+2, anchor=N, text=str(dataSetC[x][0]))
					else:
						c.create_text(0.5*(x0+x1), y0-2, anchor=S, text=str(dataSetC[x][0]))
        daystring = DAYS[(tday+x)%7]
        #if x==0 :
					#daystring="today"
        c.create_text(0.5*(x0+x1), y1+20, text=daystring,font=("Helvectica", "9"))
        
    c.create_text(80, 20, anchor=SW, text="Workload in the next few days:")
    c.create_line(0, zero[1] , int(float(WIDTH)*0.4999) , zero[1], width=2)
    c.create_line( zero[0], zero[1] - 0.75*zero[1]  , zero[0], zero[1]+D1 , width=2)
    c.create_line( zero, zero[0]-D1*0.9, zero[1]+D1*0.9)
    c.create_text(0, zero[1]+D1*0.2, anchor=W, text="Cards")
    c.create_text(D1*0.45, zero[1]+D1*0.8, anchor=W, text="Day")
    
    c1 = Canvas(Stats, width=int(float(WIDTH)*0.47), height=int(WIDTH*0.6)) 
    c1.grid(row=1 , column=1, sticky=W+E)

    c1.create_text(160, 20, anchor=SW, text="Level status:")
   
    coords= float(WIDTH)*0.05, float(WIDTH)*0.15 -35 ,float(WIDTH)*0.45,float(WIDTH)*0.55 -35

    center = 0.5 *(coords[0] +coords[2]), 0.5*(coords[1]+coords[3])

    counter = 0
    initialvalue=0.0
    pie_data=[center,dir]
    sectors=[[0,0]]
    for l in range( len( dataSetB )):
			if(l>0):
				w0 = frac(dataSetB[l-1])
			else:
				w0 = initialvalue			
			w1 = frac(dataSetB[l] - 1e-10)
			initialvalue+=w0
			#print "color = "+getColor(counter)
			color, foo = getColor(counter, len(dataSetB))
			c1.create_arc( coords , fill=color, start=initialvalue, extent=w1, width=2 ,activewidth=4, outline="grey50" )
			sectors.append([w1+sectors[-1][0],l])
			#if( int(round(dataSetB[l+1]*numCards,0)) > 0 ):
				#textPos = center[0] + distance*cos(winkel(initialvalue +0.5*w1)), center[1] -  distance*sin(winkel(initialvalue +0.5*w1))
				#c1.create_text( textPos , text="Level "+ str(l+1) + " (" + str(int(round(dataSetB[l+1]*100.0,0))) + "%)")
			
			counter += 1
    pie_data.append(sectors)
				

    distance = 0.37*(coords[2]-coords[0]) 
    initialvalue=0.0
    for l in range( len( dataSetB ) ):
			if(l>0):
				w0 = frac(dataSetB[l-1])
			else:
				w0 = initialvalue
			w1 = frac(dataSetB[l])
			initialvalue+=w0
			if( int(round(dataSetB[l]*numCards,0)) > 0 ):
				textPos = center[0] + distance*cos(winkel(initialvalue +0.5*w1)), center[1] -  distance*sin(winkel(initialvalue +0.5*w1))
				#if l >0 :
				c1.create_text( textPos , text=str(l) + " (" + str(int(round(dataSetB[l]*100.0,0))) + "%)",font=("Helvectica", "12"))
				#else:
					#c1.create_text( textPos , text="N (" + str(int(round(dataSetB[l]*100.0,0))) + "%)",font=("Helvectica", "12"))
       
    c1.bind("<Button-1>",lambda e:show_pie_level(e,pie_data,0.5*(coords[2]-coords[0])))
    #c1.create_text(center[0],470,  text="Ln: Cards on level n,  N: New Cards")
    Label(Stats,height = 6).grid(row=8, columnspan=100)
    Label(top,font=("Helvetica",8),text="Copyright (c) 2012: Can Oezmen, Axel Pfeiffer",height = 1).grid(row=2, sticky=S,columnspan=100)
    
    color, dl = getColor(0, len(dataSetB))
    ybasis = 420
    c1.create_rectangle( coords[0], ybasis , coords[0] + 20, ybasis +18,width=0, fill=color  )
    c1.create_text( coords[0]+25, ybasis+9, anchor=W, text = "Level 0 (new)" )
    color, dl = getColor(1, len(dataSetB))
    c1.create_rectangle( coords[0], ybasis+20, coords[0] + 20, ybasis +38,width=0, fill= color )
    c1.create_text( coords[0]+25, ybasis+29, anchor=W, text = "Level 1 (bad)" )
    color, dl = getColor(2, len(dataSetB))
    c1.create_rectangle( coords[0], ybasis+40, coords[0] + 20, ybasis +58,width=0, fill= color )
    c1.create_text( coords[0]+25, ybasis+49, anchor=W, text = "Level 2 (improving)" )
    
    if( len(dataSetB)-1 >2 ):
			color, dl = getColor(3, len(dataSetB))
			c1.create_rectangle( coords[0]+150, ybasis, coords[0] + 170, ybasis+18,width=0, fill= color )
			c1.create_text( coords[0]+175, ybasis+9, anchor=W, text = "Level 3 - "+str(2+dl)+" (good)" )

    if( len(dataSetB)-1 >2+dl ):
			color, dl = getColor(int( 0.5*(len(dataSetB)+3)), len(dataSetB)) 
			c1.create_rectangle( coords[0]+150, ybasis+20, coords[0] + 170, ybasis+38,width=0, fill= color )
			c1.create_text( coords[0]+175, ybasis+29, anchor=W, text = "Level "+str(2+dl+1)+" - "+str(2+2*dl)+" (excellent)" )

    if( len(dataSetB)-1 >2+dl*2 ):
			color, dl=getColor(len(dataSetB)-1, len(dataSetB)) 
			c1.create_rectangle( coords[0]+150, ybasis+40, coords[0] + 170, ybasis+58,width=0, fill= color )
			c1.create_text( coords[0]+175, ybasis+49, anchor=W, text = "Level "+str(2+2*dl+1)+" - "+str(len(dataSetB)-1)+" (outstanding)" )
    mainloop()


def frac(n): return 360. * n


def winkel(w): return float(w)* pi/180.0


def show_pie_level(event,pie_data,radius):
	dir=pie_data[1]	
	center=pie_data[0]
	relX = center[0] - event.x
	relY=center[1]-event.y
	if sqrt(relX*relX+relY*relY)<=radius:
		angle_rad=atan2(relY,relX)
		degree = ((angle_rad + pi) * 180 / pi)
		degree=(degree-360)*(-1)
		for i in range(0,len(pie_data[2])-1):
			if degree<=pie_data[2][i+1][0] and degree>=pie_data[2][i][0]:
				level=pie_data[2][i+1][1]
				break
		all_fcs=get_all_fcs(dir)
		fcs={}
		for elem in all_fcs:
			if all_fcs[elem]['level']==str(level):
				fcs[elem]={"tag":elem,"dir":all_fcs[elem]['folder'],"level":str(all_fcs[elem]['level'])}
		display_mult_fcs(fcs,"%s flashcard(s) at level %s in %s"%(str(len(fcs)),str(level),dir.split("/")[-1]),"Go Back","lambda:statistics_nextWeek('%s')"%(dir),"./.TexFlasher/stat.png")


#################################################################################### Get FC Info

def get_fc_info(dir,tag,ldb=None):
	if not ldb:
		ldb=load_leitner(dir,user)
	for elem in ldb.childNodes:
		if elem.tagName==tag:
			return elem	
			break



	 
def get_fc_desc(tex_file_path):
	try:
		tex_file=open(tex_file_path,"r")
	except:
		print "Fatal Error: Cannot open file: "+tex_file_path+"!"
		sys.exit()	
	type=""
	content=""
	beg_con=False
	theorems={}
	for line in tex_file:
		if re.compile('newtheorem.*?\{(.*?)\}.*?\{(.*?)\}.*?').findall(line):
			matches=re.compile('newtheorem.*?\{(.*?)\}.*?\{(.*?)\}.*?').findall(line)		
			theorems[matches[0][1]]=matches[0][0]
		if re.compile('begin\{flashcard\}\{.*?(.*?)\}\n').findall(line):
			fc_name=re.compile('begin\{flashcard\}\{.*?(.*?)\}\n').findall(line)[0]	
			try:
				theorem_name,title=fc_name.split(": ")
				theorem_type=theorems[theorem_name]
			except:
				title=fc_name
				theorem_type=""
				theorem_name=""
			beg_con=True
		if beg_con and not re.compile('end\{flashcard\}').findall(line) and not re.compile('begin\{flashcard\}\{.*?(.*?)\}\n').findall(line) and not re.compile('flushleft').findall(line) and not re.compile('footnotesize').findall(line):
			content+=line
		elif 	re.compile('end\{flashcard\}').findall(line):
			beg_con=False
	return title,theorem_name,theorem_type,content
		


############################################################### Search ###########################################
				
def search_flashcard(event="none"):
	search_query=query.get()
	# set similarity sensitivity
	thresh=0.7 #marker and title
	content_thresh=0.8 # content
	if len(search_query)>0 and not search_query=="query ...":		
		match_list=[]
		match_info={}
		match_info_name={}
		match_info_content={}
		all_fcs=get_all_fcs()
		for fc_elem in all_fcs:
			match_list.append(fc_elem)	
			fc_name,theorem_name,theorem_type,fc_content=get_fc_desc(all_fcs[fc_elem]['folder']+'/Karteikarten/'+fc_elem+'.tex')
			match_info_content[fc_content]=[fc_elem,all_fcs[fc_elem]['folder']]
			match_info_name[fc_name+" "+theorem_name]=[fc_elem,all_fcs[fc_elem]['folder']]
			match_info[fc_elem]=[fc_elem,all_fcs[fc_elem]['folder']]		
		#search marker
		result_marker=get_close_matches(search_query,match_list,cutoff=thresh)
		search_results={}
		for res in result_marker:
			search_results[match_info[res][0]]={"tag":match_info[res][0],"dir":match_info[res][1],"level":all_fcs[match_info[res][0]]['level']}	
		#search title
		for res in match_info_name:
			if not len(search_query.split(" "))>0:
				if len(get_close_matches(search_query.lower(),res.lower().split(" "),cutoff=thresh))>0:			
					search_results[match_info_name[res][0]]={"tag":match_info_name[res][0],"dir":match_info_name[res][1],"level":all_fcs[match_info_name[res][0]]['level']}
			else:
				match_count=0
				for s in search_query.lower().split(" "):
					if len(get_close_matches(s,res.lower().split(" "),cutoff=thresh))>0 or len(get_close_matches(s,[res.lower()],cutoff=thresh))>0 or len(get_close_matches(s,res.lower().split("-"),cutoff=thresh))>0:						
						match_count+=1
				if match_count==len(search_query.split(" ")):
					search_results[match_info_name[res][0]]={"tag":match_info_name[res][0],"dir":match_info_name[res][1],"level":all_fcs[match_info_name[res][0]]['level']}						
		#search content	
		if check.var.get()==1:	
			for res in match_info_content:
				if not len(search_query.split(" "))>0:
					if len(get_close_matches(search_query.lower(),res.lower().split(" "),cutoff=content_thresh))>0:			
						search_results[match_info_content[res][0]]={"tag":match_info_content[res][0],"dir":match_info_content[res][1],"level":all_fcs[match_info_content[res][0]]['level']}
				else:
					match_count=0
					for s in search_query.lower().split(" "):
						if len(get_close_matches(s,res.lower().split(" "),cutoff=content_thresh))>0 or len(get_close_matches(s,[res.lower()],cutoff=thresh))>0 or len(get_close_matches(s,res.lower().split("-"),cutoff=content_thresh))>0:						
							match_count+=1
					if match_count==len(search_query.split(" ")):
						search_results[match_info_content[res][0]]={"tag":match_info_content[res][0],"dir":match_info_content[res][1],"level":all_fcs[match_info_content[res][0]]['level']}																				
		## display search results
		if len(search_results)>1:
			display_mult_fcs(search_results,version+" - Found "+str(len(search_results))+" search results for \""+search_query+"\"","Menu","lambda:menu()","./.TexFlasher/menu.png")
			default_search_value.set("query ...")	

		elif len(search_results)==1:
			for res in search_results:
				disp_single_fc(search_results[res]['dir']+'/Karteikarten/'+search_results[res]['tag']+'-1.jpg',search_results[res]['tag']+" in "+search_results[res]['dir'].split("/")[-1]+' level '+search_results[res]['level'],search_results[res]['tag'])
				default_search_value.set("query ...")	
				break
		else:
			default_search_value.set( defaultAnswer( query.get().lower() ) )
	else:
		default_search_value.set("query ...")


def defaultAnswer( arg ):
	ANSWERS={ 
					user:"You are one lazy student.",
					"can":"Can is a great programmer!",
					"axel":"Axel is a great programmer!",
					"david":"David sucks at OA!",
					"meaning of life":"42!",
					"what is the meaning of life":"42!",
					"what is the meaning of life?":"42!"
					}
	
	if arg in ANSWERS:
		return ANSWERS[arg]
	else:
		return "Nothing found!"
	
############################################################### display flashcards ###########################################################	

class AutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)		
    def pack(self, **kw):
        raise TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise TclError, "cannot use place with this widget"

# TODO Alter schwede, size=BOOL(>1) (=true) size>1 oder was?
def create_image_button(window,path,width=None,height=None):
	button_image = Image.open(path)
	if width and height:
		STRS=path.partition("-0")
		thumbname=STRS[0]+"-thumb"+str(int(width))+"x"+str(int(height))+STRS[2]
		if os.path.isfile(thumbname):
			try:
				button_image = Image.open(thumbname)
			except:
				button_image = button_image.resize((width, height), Image.ANTIALIAS)
		else:
			button_image = button_image.resize((width, height), Image.ANTIALIAS)
	img= ImageTk.PhotoImage(button_image)
	button=Button(window,image=img,bd=BD)
	button.img=img
	button.grid()
	return button


def get_all_fcs(path=False):
	all_fcs = {}
	if os.path.isfile("./.TexFlasher/config.xml"):
		tree = xml.parse("./.TexFlasher/config.xml")
		config_xml = tree.getElementsByTagName('FlashFolder')
		for elem in config_xml:
			if path and path==os.path.dirname(elem.getAttribute('filename')):			
				dir=os.path.dirname(elem.getAttribute('filename'))
				try:
					tree = xml.parse(dir+"/Users/"+user+".xml")
					dir_xml = tree.getElementsByTagName('ldb')[0].childNodes
					for fc_elem in dir_xml:
						all_fcs[fc_elem.tagName]={"folder":dir,"level":fc_elem.getAttribute('level')} # add atributes as needed
				except:
					pass
			elif not path and not elem.getAttribute('filename')=="":
				dir=os.path.dirname(elem.getAttribute('filename'))
				try:
					tree = xml.parse(dir+"/Users/"+user+".xml")
					dir_xml = tree.getElementsByTagName('ldb')[0].childNodes
					for fc_elem in dir_xml:
						all_fcs[fc_elem.tagName]={"folder":dir,"level":fc_elem.getAttribute('level')} # add atributes as needed
				except:
					pass
	return all_fcs	


def display_mult_fcs(fcs,title,button_title,button_command,button_image): #Syntax: fcs={"anykey":{"tag":fc_tag,"dir":fc_dir,"level":fc_level}, ...}
	clear_window()
	global search_canvas # scrolling wheel support needs that for some reason
	top.title(title)
	Label(top,font=("Helvetica",8),text="Copyright (c) 2012: Can Oezmen, Axel Pfeiffer", height =2).grid(row=3, sticky=S,columnspan=2)	
	exec('menu_button=create_image_button(top,"'+button_image+'",40,40)')
	exec('menu_button.configure(text="%s",command=%s)'%(button_title,button_command))
	exec('menu_button.grid(row=0,columnspan=2)')
	#Label(top,height=1).grid(row=1,columnspan=2)	
	vscrollbar = AutoScrollbar(top)
	vscrollbar.grid(row=2, column=2, sticky=N+S)
	search_canvas = Canvas(top,yscrollcommand=vscrollbar.set)
	search_canvas.grid(row=2, column=0, sticky=N+S+E+W)
	vscrollbar.config(command=search_canvas.yview)
	Search_frame = Frame(search_canvas,border=10)
	#Search_frame.rowconfigure(1, weight=1)
	Search_frame.columnconfigure(0, weight=1)
	Search_frame.grid(row=0,column=0)
	Label(Search_frame,width=1).grid(column=2,rowspan=100)
	i=0 #start at row	
	 #width of the images
	iterator=fcs.__iter__()
	images_row=[1,3] # increaese number of images per row by adding [1,3,6,9, ...]
	size=WIDTH/len(images_row)-40
	for res in iterator:
		for colu in images_row:
			if colu>images_row[0]:
				try:
					res=iterator.next()
				except:
					break
			button=create_image_button(Search_frame,fcs[res]['dir']+"/Karteikarten/"+fcs[res]['tag']+"-0.jpg",size,int(size*0.6))
			exec('button.configure(command=lambda:disp_single_fc("'+fcs[res]['dir']+"/Karteikarten/"+fcs[res]['tag']+"-1.jpg"+'","'+fcs[res]['tag']+' in '+fcs[res]['dir'].split("/")[-1]+' level '+fcs[res]['level']+'","'+fcs[res]['tag']+'"))')
			button.grid(row=str(i+1),column=colu)
			exec("button.bind('<Button-4>', lambda event: search_canvas.yview_scroll(-1, UNITS))")
			exec("button.bind('<Button-5>', lambda event: search_canvas.yview_scroll(1, UNITS)) ")
			dist=Label(Search_frame,height=1).grid(row=str(i+2),column=colu)
		i+=3
	search_canvas.create_window(0, 0, anchor=NW, window=Search_frame)
	exec("Search_frame.bind('<Button-4>', lambda event: search_canvas.yview_scroll(-1, UNITS))")
	exec("Search_frame.bind('<Button-5>', lambda event: search_canvas.yview_scroll(1, UNITS)) ")			
	exec("search_canvas.bind('<Button-4>', lambda event: event.widget.yview_scroll(-1, UNITS))")
	exec("search_canvas.bind('<Button-5>', lambda event: event.widget.yview_scroll(1, UNITS)) ")
	Search_frame.update_idletasks()
	search_canvas.config(scrollregion=search_canvas.bbox("all"),width=WIDTH-10,height=HEIGHT-60)


def  disp_single_fc(image_path,title,tag):
	# create child window
	win = Toplevel()
	# display message
	win.title(title)
	win.iconbitmap(iconbitmapLocation)
	win.iconmask(iconbitmapLocation)
	fc_image = Image.open(image_path)
	fc_image = fc_image.resize((WIDTH, int(WIDTH*0.6)), Image.ANTIALIAS)
	search_flashcard_1 = ImageTk.PhotoImage(fc_image)	
	fc_image_b_1=Button(win,image=search_flashcard_1,command=win.destroy)
	fc_image_b_1.img=search_flashcard_1
	fc_image_b_1.grid(row=1,column=0,columnspan=2)	
	ldb=load_leitner_db(os.path.dirname(image_path)+"/../",user)
	fc_info=get_fc_info(os.path.dirname(image_path)+"/../",tag,ldb)

	button=create_image_button(win,"./.TexFlasher/edit.png",40,40)
	button.configure(command=lambda:edit_fc(fc_image_b_1,os.path.dirname(image_path).replace("/Karteikarten",""),tag,win))
	button.grid(row=1,column=1,sticky=E+N)	
	
	comment_b=create_image_button(win,"./.TexFlasher/comment.png",40,40)
	comment_b.configure(command=lambda:create_comment_canvas(fc_image_b_1,os.path.dirname(image_path).replace("/Karteikarten",""),tag,win))
	comment_b.grid(row=1,column=0,sticky=N+W)
	Label(win,height=1).grid(row=2,column=0)
	reset_level=1
	Label(win,text="Created: "+fc_info.getAttribute("created")+", Last Reviewed:"+fc_info.getAttribute("lastReviewed")).grid(row=0,columnspan=2)	
#	if tag in changed:		
#		button=Button(win,bd=BD,text="Set to Level %s"%reset_level,command=lambda:update_flashcard(tag,ldb,os.path.dirname(image_path)+"/../","Level",reset_level,strftime("%Y-%m-%d %H:%M:%S", gmtime(0)),True)).grid(row=3,column=1,sticky=W)




###############################################################  Edit fc ######################################################################

def edit_fc(image_b,dir,fc_tag,window):
	fc_name,theorem_name,theorem_type,content=get_fc_desc(dir+"/Karteikarten/"+fc_tag+".tex")

	main_c = Canvas(window)
	main_c.grid(row=1,rowspan=10,columnspan=10,sticky=N+E+W+S)

	frame=Frame(main_c,border=10)
	frame.columnconfigure(0, weight=1)
	frame.columnconfigure(0, weight=1)	
	frame.grid(sticky=E+W+N+S)

	edit_text=Text(frame,width=int(WIDTH*0.139),height=int(WIDTH*0.045))
	edit_text.insert(INSERT,content)
	edit_text.grid(row=0,column=0,columnspan=2,sticky=N+W+E+S)
	
	edit_save=Button(frame,bd=BD)
	edit_save.configure(text="Save",command=lambda:save_edit(image_b,edit_cancel,edit_save,edit_text,dir,fc_tag,theorem_type,main_c))
	edit_save.grid(row=1,column=0,sticky=W+S)	
	edit_cancel=Button(frame,bd=BD)
	edit_cancel.configure(text="Cancel",command=lambda:cancel_edit(main_c))	
	edit_cancel.grid(row=1,column=1,sticky=E+S)


def cancel_edit(main_c):
	main_c.grid_forget()	


def change_latex(file_path,fc_tag,content,theorem_type):
	file=open(file_path,"r")
	tag=False
	new_latex=[]

	old_fcs=[]
	new_fcs=[]

	for line in file:
		if re.compile("%fc=").findall(line):
			old_fcs.append(line)
		if re.compile('%fc='+fc_tag+'\n').findall(line):	
			tag=True
			new_latex.append(line)
		if re.compile('begin\{'+theorem_type+'\}').findall(line) and tag:
			new_latex.append(line+content)
		if re.compile('end\{'+theorem_type+'\}\n').findall(line) and tag:	
			tag=False
		if not tag:
			new_latex.append(line)
	file.close()
	for line in new_latex:
		if re.compile("%fc=").findall(line):
			new_fcs.append(line)	
	if old_fcs==new_fcs:
		new_file=open(file_path,"w")
		for line in new_latex:
			new_file.writelines(line)
		new_file.close()
	else:
		raise	
	
def save_edit(b_image,edit_cancel,edit_save,edit_text,dir,fc_tag,theorem_type,main_c):
	content=edit_text.get('1.0', END)
	if os.path.isfile("./.TexFlasher/config.xml"):
		try:
			tree = xml.parse("./.TexFlasher/config.xml")
			config_xml = tree.getElementsByTagName('config')[0]
			for elem in config_xml.childNodes:
				if os.path.dirname(elem.getAttribute('filename'))==dir:
					change_latex(elem.getAttribute('filename'),fc_tag,content,theorem_type)				
					executeCommand("bash .TexFlasher/recompileFlashcards.sh "+elem.getAttribute('filename'), True)
					image = Image.open(os.path.dirname(elem.getAttribute('filename'))+"/Karteikarten/"+fc_tag+"-1.jpg")
					image = image.resize((WIDTH, int(WIDTH*0.6)), Image.ANTIALIAS)
					flashcard = ImageTk.PhotoImage(image)
					b_image.configure(image=flashcard)
					b_image.img=flashcard					
					break
		except:
			tkMessageBox.showerror("Error","Fatal error while saving new content for %s!"%fc_tag)
	cancel_edit(main_c)
	
########################################################## Comment on fc ##############################################################

def create_comment_canvas(image_b,dir,fc_tag,win):
	
        class RectTracker:	
	  def __init__(self, canvas):
		self.canvas = canvas
		self.item = None
		
	  def draw(self, start, end, **opts):
		"""Draw the rectangle"""
		return self.canvas.create_rectangle(*(list(start)+list(end)), **opts)
		
          def autodraw(self, **opts):
		"""Setup automatic drawing; supports command option"""
		self.start = None
		self.canvas.bind("<Button-1>", self.__update, '+')
		self.canvas.bind("<B1-Motion>", self.__update, '+')
		self.canvas.bind("<ButtonRelease-1>", self.__stop, '+')
		
		self._command = opts.pop('command', lambda *args: None)
		self.rectopts = opts
		
	  def __update(self, event):
		if not self.start:
			self.start = [event.x, event.y]
			return
		
		if self.item is not None:
			self.canvas.delete(self.item)
		self.item = self.draw(self.start, (event.x, event.y), **self.rectopts)
		self._command(self.start, (event.x, event.y))
		
	  def __stop(self, event):
		self.start = None
		self.canvas.delete(self.item)
		self.item = None
		

        global b1, xold, yold,linestate
	points = []
	spline = 0
	tag1 = "theline"
	b1="up"
	xold, yold = None, None
	eraseswitch=0
	x1=-1 
	y1=-1
	recswitch=0
	r1=-1
	r2=-1
        linestate=1
	main_c = Canvas(win)
	main_c.grid(row=1,rowspan=10,columnspan=10,sticky=N+E+W+S)
	frame=Frame(main_c)
	frame.grid(row=0,columnspan=5,sticky=N+S+W+E)
	c=Canvas(frame,width=WIDTH,height=WIDTH*0.6)

	image = Image.open(dir+"/Karteikarten/"+fc_tag+"-1.jpg")
	image = image.resize((WIDTH, int(WIDTH*0.6)), Image.ANTIALIAS)
	flashcard = ImageTk.PhotoImage(image)
	back_img=c.create_image(int(WIDTH/2), int(WIDTH*0.3), image=flashcard)
	c.img=flashcard	
	c.grid(row=0,columnspan=5,sticky=N+E+W+S)
        rect = RectTracker(c)
        rect.autodraw(fill="", width=2, command=onDrag)

	if os.path.isfile(dir+"/Karteikarten/"+fc_tag+"_comment.png"):
		im = Image.open(dir+"/Karteikarten/"+fc_tag+"_comment.png")
		image = Image.open(dir+"/Karteikarten/"+fc_tag+"_comment.png")
		comment = ImageTk.PhotoImage(image)		
		c.create_image(int(WIDTH/2), int(WIDTH*0.3), image=comment)
		c.comment=comment	

	
        li =  Button (frame, text="paint", command=lambda: changelinestate(li))
	w = Button (frame, text="save", command=lambda:savefile(main_c,c,dir,fc_tag))
	v = Button (frame, text="clear all", command=lambda:clearall(c,dir,fc_tag,w))
	cancel = Button (frame, text="Cancel", command=lambda:cancel_edit(main_c))

	c.configure(cursor="spraycan")
        li.grid(row=2,column=1)
	w.grid(row=2, column=3)
	v.grid(row=2, column=2)
	cancel.grid(row=2,column=4)
	c.bind("<Motion>", lambda event: motion(event,w,c))
	c.bind("<ButtonPress-1>", b1down)
	c.bind("<ButtonRelease-1>",b1up)
		

def onDrag(start, end):
		global x,y
		
def kill_xy(c,event=None):
		c.delete('no')

def savefile(main,canvas,dir,tag):
	canvas.img=None
        canvas.delete('no')
	canvas.postscript(file=dir+"/Karteikarten/"+tag+"_comment.eps")
	os.popen("convert -resize 117.82% -verbose -colorspace RGB "+dir+"/Karteikarten/"+tag+"_comment.eps -fill none "+dir+"/Karteikarten/"+tag+"_comment.png")
	cancel_edit(main)

def b1down(event):
 global b1
 b1="down"

def b1up(event):
 global b1, xold, yold
 b1="up"
 xold= None
 yold= None

def motion(event,w,c):
  if b1 == "down":
   global xold, yold,linestate
   if linestate is 0 and (xold is not None and yold is not None):
     event.widget.create_line(xold,yold,event.x,event.y,smooth=TRUE,fill="red",width=min(pow(abs(xold-event.x)^2+abs(yold-event.y)^2,0.5),5))
     w.config(state=NORMAL)
   elif (xold is not None and yold is not None):
     event.widget.create_line(xold,yold,event.x,yold,smooth=TRUE,fill="blue",width=3)
     w.config(state=NORMAL)
   if linestate is 0:
     xold = event.x
     yold = event.y
   else: 
     xold = event.x
     if yold is None:
       yold = event.y
  global x, y
  kill_xy(c)
  dashes = [3, 2]
  x = c.create_line(event.x, 0, event.x, 1000, dash=dashes, tags='no')
  y = c.create_line(0, event.y, 1000, event.y, dash=dashes, tags='no')

def clearall(canvas,dir,fc_tag,w):
 canvas.delete("all")
 os.system("rm -f "+dir+"/Karteikarten/"+fc_tag+"_comment.eps")
 os.system("rm -f "+dir+"/Karteikarten/"+fc_tag+"_comment.png")
 canvas.create_image(int(WIDTH/2), int(WIDTH*0.3), image=canvas.img)
 w.config(state=DISABLED)


def changelinestate(li):
 global linestate
 if linestate is 1:
  linestate=0
  li.config(relief=SUNKEN)
 else:
   linestate=1
   li.config(relief=RAISED)


def eraseclick(event):
 global x1
 global y1

 if (eraseswitch is 1 and x1 is -1 and y1 is -1):
   x1 = event.x
   y1 = event.y
 elif (eraseswitch is 1 and x1 is not -1 and y1 is not -1):    
   event.widget.create_oval(x1,y1,event.x,event.y,fill="white",width=0)
   x1=-1
   y1=-1   


 
def erase():
 global eraseswitch
 if eraseswitch is 0:
  eraseswitch=1
  r.config(relief=SUNKEN)
 else: 
  eraseswitch=0
  r.config(relief=RAISED)
 c.bind("<Button-1>", eraseclick)



############################################################### run flasher ###########################################################
	
def reactAndInit(selected_dir,agenda,ldb, status, listPosition,b_true,b_false,b_image):
	# this is always true except for the very first run!
	if( listPosition >=0 ):
		flashcard_name=agenda[listPosition][0]
		if status:
			#print "answer correct"
			flashcard=ldb.getElementsByTagName(flashcard_name)[0]
			current_level=int(flashcard.getAttribute('level'))
			if current_level == 0:
				update_flashcard(flashcard_name,ldb,selected_dir,"Level",2)
			else:
				update_flashcard(flashcard_name,ldb,selected_dir,"Level",current_level+1)
		else:
			#print "answer wrong"
			update_flashcard(flashcard_name,ldb,selected_dir,"Level",1)
	
	if( listPosition < 0 or listPosition%10 == 9 ):
		# look for updates at the beginning and every 10 fcs
		checkForUpdate()
		
	listPosition +=1
	if ( len(agenda) > listPosition):
		flashcard_name=agenda[listPosition][0]
	else:
		#print "reached end of vector"
		statistics_nextWeek(selected_dir)
		sys.exit()
	image = Image.open(selected_dir+"/Karteikarten/"+flashcard_name+"-0.jpg")
	image = image.resize((WIDTH, int(WIDTH*0.6)), Image.ANTIALIAS)
	flashcard_image = ImageTk.PhotoImage(image)
	b_image.configure(image=flashcard_image,command=lambda:answer(selected_dir,agenda,ldb, flashcard_name, listPosition,b_true,b_false,b_image))
	b_image.grid(row=1 , columnspan=2)
	b_true.configure(state=DISABLED)
	b_false.configure(state=DISABLED)
	flashcardsTodo=len(agenda)
	totalNumberCards=len(ldb.childNodes)
	e0=Label(top,anchor=W,text="  "+user+": flashcards (left today / total number): "+str(flashcardsTodo-listPosition)
	   +" / "+str(totalNumberCards), width=45).grid(row=0, columnspan=2,sticky=W)	   
	level = ldb.getElementsByTagName(flashcard_name)[0].getAttribute('level')
	#color, foo = getColor( int(level), 7)
	e1=Label(top,anchor=E,text="marker: "+flashcard_name+",  level: "+ str(level) +"  ",  width=40).grid(row=0, columnspan=2,sticky=E)
	Label(top,font=("Helvetica",8),text="Copyright (c) 2012: Can Oezmen, Axel Pfeiffer",width=int(100.0*float(WIDTH/1000.))).grid(row=3, sticky=S,columnspan=5)
		
	mainloop()


	
def answer(selected_dir,agenda,ldb, flashcard_tag, listPosition,b_true,b_false,b_image):
	image = Image.open(selected_dir+"/Karteikarten/"+flashcard_tag+"-1.jpg")
	image = image.resize((WIDTH, int(WIDTH*0.6)), Image.ANTIALIAS)
	flashcard = ImageTk.PhotoImage(image)
	b_image.configure(image=flashcard)
	b_image.img=flashcard

	b_true.configure(state=NORMAL,command=lambda:reactAndInit(selected_dir,agenda,ldb,True, listPosition,b_true,b_false,b_image))
	b_false.configure(state=NORMAL,command=lambda:reactAndInit(selected_dir,agenda,ldb,False, listPosition,b_true,b_false,b_image))
	edit_b=create_image_button(top,"./.TexFlasher/edit.png",40,40)
	edit_b.configure(command=lambda:edit_fc(b_image,selected_dir,flashcard_tag,top))
	edit_b.grid(row=1,column=1,sticky=N+E)
	comment_b=create_image_button(top,"./.TexFlasher/comment.png",40,40)
	comment_b.configure(command=lambda:create_comment_canvas(b_image,selected_dir,flashcard_tag,top))
	comment_b.grid(row=1,column=0,sticky=N+W)

	mainloop()


def run_flasher(selected_dir, stuffToDo=True ):
	clear_window()
	top.title(version+" - "+selected_dir)
	menu_button=create_image_button(top,"./.TexFlasher/menu.png",40,40)
	menu_button.configure(text="Menu",command=lambda:menu())
	menu_button.grid(row=0,columnspan=2)
	ldb=load_leitner_db(selected_dir,user)
	if( stuffToDo ):
		date = datetime.now()
	else:
		date = datetime.now()+timedelta(days=1000)
		
	agenda,new=load_agenda(ldb,selected_dir, date)
	b_image=Button(top)
	b_image.grid(row=1 , columnspan=2)
	# true flase buttons
	b_true=create_image_button(top,"./.TexFlasher/Flashcard_correct.png")
	b_false=create_image_button(top,"./.TexFlasher/Flashcard_wrong.png")
	b_true.configure(bd=BD) 
	b_false.configure(bd=BD) 
	b_true.grid(row=2, column=0, pady=int(HEIGHT*0.02/7.) )
	b_false.grid(row=2, column=1, pady=int(HEIGHT*0.02/7.) )
	reactAndInit(selected_dir,agenda,ldb, True , -1 ,b_true,b_false,b_image)

############################################################## Menu ####################################################################

def create_new():
	file = tkFileDialog.askopenfilename(parent=top,title='Choose a LaTeX file',initialdir='./',defaultextension=".tex",filetypes=[("all files","*.tex")])
	if file != None:
		filename=os.path.basename(file)
		update_config(file)
		menu()


def hide_FlashFolder(filename):
	tree = xml.parse("./.TexFlasher/config.xml")
	config_xml = tree.getElementsByTagName('config')[0]
	for elem in config_xml.childNodes:
		if elem.getAttribute('filename')==filename:
			config_xml.removeChild(elem)
	xml_file = open("./.TexFlasher/config.xml", "w")
	config_xml.writexml(xml_file)
	xml_file.close()
	menu()


def reset_flash(filename):
	if tkMessageBox.askyesno("Reset", "Do you really want to delete all learning progress for %s?"% filename.split("/")[-2]):
		file=open(os.path.dirname(filename)+"/Users/"+user+".xml","w")
		file.close()
		hide_FlashFolder(filename)
	menu()


def clear_window():
	for widget in top.grid_slaves():
		widget.grid_forget()

	
def get_log_status(filedir):
	message=""
	window_type="showinfo"
	if os.path.isfile(filedir+"/texFlasher.log"):
		log_time=ctime(os.path.getmtime(filedir+"/texFlasher.log"))
		message="Log from %s\\n\\n"%log_time
		log=open(filedir+"/texFlasher.log","r")
		for l in log:
			if re.compile('Error').findall(l):
				window_type="showerror"
						
			message+=l.replace("\n","\\n\\n")	
	else:
		message="No logfile found!"	
	return message,window_type


def show_log(filedir):
	message,window_type=get_log_status(filedir)
	exec('tkMessageBox.'+window_type+'( "Parse LaTex Logfile","%s")'%message)
        return


def saveFiles( files ):
	executeCommand( "bash .TexFlasher/save.sh "+ files, True )
	menu()
	#os.system("bash .TexFlasher/save.sh "+ files )

def checkForUpdate():
	files=""
	if os.path.isfile("./.TexFlasher/config.xml"):
		tree = xml.parse("./.TexFlasher/config.xml")
		config_xml = tree.getElementsByTagName('config')[0]
		for elem in config_xml.childNodes:
			if elem.tagName=="FlashFolder" and not elem.getAttribute('filename')=="":
				files += str(elem.getAttribute('filename')) + " "
				#files += str(os.path.dirname(elem.getAttribute('filename'))+"/Users/"+user+".xml ")
	os.system( "bash .TexFlasher/checkForUpdate.sh "+ files + "&")
	

def checkIfNeedToSave( files ):
	process = subprocess.Popen(['bash', '.TexFlasher/checkIfNeedToSave.sh', files], stdout=subprocess.PIPE)
	output  = process.stdout.read()
	
	if str(output) == "":
		return False
	else:
		return True
		
def executeCommand( command ,wait=False):

	
	win = Toplevel()
	cmd="\""+str(command)+"; exit; sh\""
	if not wait:
		os.system('xterm -geometry 110x42 -sb -e '+ cmd +' &' )
	else:
		os.system('xterm -geometry 110x42 -sb -e '+ cmd )		
	win.destroy()


def open_tex(filepath):
	try:
		os.system("(nohup "+sys.argv[1]+" "+filepath+" > /dev/null &) 2> /dev/null")
	except:
		tkMessageBox.showerror( "LaTeX Editor Variable","Please check, if your LaTeX Editor is set correctly in run-TexFlasher.sh")


def clear_search(event):
	default_search_value.set("")
	query.configure(textvariable=default_search_value)


def update_texfile( fname ):	
	executeCommand( "svn up "+os.path.dirname(fname)+"/Users/"+user+".xml; svn up "+fname, True )
	# NOTE individual hack that saves me some conflicts, we can discuss that tomorrow
	#os.system( "svn up "+os.path.dirname(fname)+"/Users/"+user+".xml > /dev/null"  )
	#os.system( "svn up "+fname+" > /dev/null" )
	os.system("rm "+os.path.dirname(fname)+"/Karteikarten/UPDATE 2>/dev/null")
	create_flashcards( fname )


def create_flashcards( filename ):
	update_config(filename)
	#os.system("bash .TexFlasher/createFlashcards.sh "+ filename)
	executeCommand("bash .TexFlasher/createFlashcards.sh "+ filename, True)
	menu()
	#run_flasher(dir_name,top)


def update_config(filename):
	dir_name=os.path.dirname(filename)
	doc=xml.Document()
	config_xml = doc.createElement('config')
	doc.appendChild(config_xml)
	if os.path.isfile("./.TexFlasher/config.xml"):
		try:
			tree = xml.parse("./.TexFlasher/config.xml")
			config_xml = tree.getElementsByTagName('config')[0]
		except:
			pass
	if not os.path.exists(filename):
		print "filename does not exist."
		menu()
	dirFound=False
	for elem in config_xml.childNodes:
		if elem.tagName=="FlashFolder" and elem.getAttribute('filename')==filename:
			elem.setAttribute('lastReviewed', strftime("%Y-%m-%d %H:%M:%S", localtime()))
			dirFound=True
	if not dirFound:
		elem=doc.createElement("FlashFolder")
		config_xml.appendChild(elem)
		now=strftime("%Y-%m-%d %H:%M:%S", localtime())
		elem.setAttribute('filename',filename)
		elem.setAttribute('lastReviewed', now)
		elem.setAttribute('created',now)	
	xml_file = open("./.TexFlasher/config.xml", "w")
	config_xml.writexml(xml_file)
	xml_file.close()


def menu():
	bordersize=2
	clear_window()
	top.title(version+" - Menu") 
	button_size=str(40)
	global saveString 
	saveString = ""
	Label(top,height=2,text="TexFlasher based on Leitner-Method",font=("Helvetica", 16)).grid(row=0,columnspan=8,sticky=E+W)
	#if os.path.isfile("UPDATE"):
		#Label(top,height=2,text="(update available)           ",fg="red",font=("Helvetica", 16)).grid(row=0,columnspan=2,sticky=E)
	Menu=Frame(top,border=10,width=int(WIDTH*1.005),height=HEIGHT*0.9)
	Menu.grid_propagate(0)
	Menu.grid(row=2,column=0,sticky=E+W)
	Menu.columnconfigure(1, weight=3)
	row_start=3
	if os.path.isfile("./.TexFlasher/config.xml"):
		tree = xml.parse("./.TexFlasher/config.xml")
		config_xml = tree.getElementsByTagName('config')[0]		
		for l in config_xml.childNodes:
			if l.tagName=="FlashFolder" and l.getAttribute('filename')!="":
				todo=0;
				length=0
				#try:
				ldb= load_leitner_db(os.path.dirname(l.getAttribute('filename')),user)
				today,new=load_agenda(ldb,os.path.dirname(l.getAttribute('filename')))
				todo=len(today)
				length=len(ldb.childNodes)
			#	except:
			#		pass
				start_column=0
				log,window_type=get_log_status(os.path.dirname(l.getAttribute('filename')))
				


				button_status="NORMAL"
				if length==0:
					button_status="DISABLED"
				new_status="NORMAL"					
				#open folder
				if todo-new>0:
					exec('button_' + str(row_start)+'_open =create_image_button(Menu,"./.TexFlasher/Flashcard_folder_red.png",60,60)')
					exec('button_' + str(row_start)+'_open.configure(border='+str(bordersize)+',width=70,state='+button_status+',command=lambda:run_flasher("'+os.path.dirname(l.getAttribute('filename'))+'", True))')	
				elif new >0:
					exec('button_' + str(row_start)+'_open =create_image_button(Menu,"./.TexFlasher/Flashcard_folder_yellow.png",60,60)')
					exec('button_' + str(row_start)+'_open.configure(border='+str(bordersize)+',width=70,state='+button_status+',command=lambda:run_flasher("'+os.path.dirname(l.getAttribute('filename'))+'", True))')
				else:
					exec('button_' + str(row_start)+'_open =create_image_button(Menu,"./.TexFlasher/Flashcard_folder.png",60,60)')
					exec('button_' + str(row_start)+'_open.configure(border='+str(bordersize)+',width=70,state='+button_status+',command=lambda:run_flasher("'+os.path.dirname(l.getAttribute('filename'))+'", False))')
									
				exec('button_' + str(row_start)+'_open.grid(row='+str(row_start)+',sticky=N+W+S+E,column='+str(start_column)+')')
				#folder desc
				exec('fc_folder_' + str(row_start)+'_desc=Label(Menu,justify=LEFT,text="'+l.getAttribute('filename').split("/")[-2]+'\\nlength: '+str(length)+'\\ntodo: '+str(todo-new)+', new: '+str(new)+'\\nupdated: '+l.getAttribute('lastReviewed')+'").grid(row='+str(row_start)+', column='+str(start_column+1)+',sticky=W)')

				#update
				if os.path.isfile(os.path.dirname(l.getAttribute('filename'))+"/Karteikarten/UPDATE"):
					update_image="./.TexFlasher/update_now.png"
				else:
					update_image="./.TexFlasher/update.png"
				if l.getAttribute('lastReviewed')==l.getAttribute('created'):
					exec('button_' + str(row_start)+'_update=create_image_button(Menu,"./.TexFlasher/update_now.png",'+button_size+','+button_size+')')
					exec('button_' + str(row_start)+'_update.configure(border='+str(bordersize)+',command=lambda:update_texfile("'+l.getAttribute('filename')+'"))')
					exec('button_' + str(row_start)+'_update.grid(row='+str(row_start)+',column='+str(start_column+2)+',sticky=W+N+S+E)')
					new_status="DISABLED"
				else:
					exec('button_' + str(row_start)+'_update=create_image_button(Menu,"'+update_image+'",'+button_size+','+button_size+')')
					exec('button_' + str(row_start)+'_update.configure(border='+str(bordersize)+',command=lambda:update_texfile("'+l.getAttribute('filename')+'"))')
					exec('button_' + str(row_start)+'_update.grid(row='+str(row_start)+',column='+str(start_column+2)+',sticky=W+N+S+E)')		

				#stats	
				exec('button_' + str(row_start)+'_stat=create_image_button(Menu,"./.TexFlasher/stat.png",'+button_size+','+button_size+')')
				exec('button_' + str(row_start)+'_stat.configure(border='+str(bordersize)+',state='+button_status+',command=lambda:statistics_nextWeek("'+os.path.dirname(l.getAttribute('filename'))+'"))')
				exec('button_' + str(row_start)+'_stat.grid(row='+str(row_start)+',column='+str(start_column+3)+',sticky=N+S+W+E)')
				#open tex file
				exec('button_' + str(row_start)+'_tex =create_image_button(Menu,"./.TexFlasher/latex.png",'+button_size+','+button_size+')')
				exec('button_' + str(row_start)+'_tex.configure(border='+str(bordersize)+',command=lambda:open_tex("'+l.getAttribute('filename')+'"))')
				exec('button_' + str(row_start)+'_tex.grid(row='+str(row_start)+',column='+str(start_column+4)+',sticky=W+N+S+E)')
				#log
				exec('button_' + str(row_start)+'_log=create_image_button(Menu,"./.TexFlasher/'+window_type+'.png",'+button_size+','+button_size+')')
				exec('button_' + str(row_start) + '_log.configure(border='+str(bordersize)+',state='+new_status+',command=lambda:show_log("'+os.path.dirname(l.getAttribute('filename'))+'"))')
				exec('button_' + str(row_start)+'_log.grid(row='+str(row_start)+',column='+str(start_column+5)+',sticky=N+S+E+W)')
				#reset
				exec('button_' + str(row_start)+'_res=create_image_button(Menu,"./.TexFlasher/delete.png",'+button_size+','+button_size+')')
				exec('button_' + str(row_start)+'_res.configure(border='+str(bordersize)+',state='+button_status+',command=lambda:reset_flash("'+l.getAttribute('filename')+'"))')
				exec('button_' + str(row_start)+'_res.grid(row='+str(row_start)+',column='+str(start_column+7)+',sticky=N+S+E)')
				saveString += " "+ os.path.dirname(l.getAttribute('filename'))+"/Users/"+user+".xml "
				saveString += " "+ l.getAttribute('filename') 
				exec('Label(Menu,height=1).grid(row='+str(row_start+1)+')')
				row_start+=2	


	#create button
	create=create_image_button(Menu,"./.TexFlasher/Flashcard_folder_add.png",60,60)
	create.configure(border=bordersize,width=70,command=create_new) 
	if row_start > 3:
		create.grid(row=1,column=0,sticky=W)
		#search field
		global query
		global default_search_value
		global check
		default_search_value = StringVar()
		query = Entry(Menu,textvariable=default_search_value,bd =5,justify=CENTER)
		query.bind('<Return>', search_flashcard)
		query.bind("<Button-1>", clear_search)
		default_search_value.set("query ...")
		query.grid(row=1,column=1,sticky=E+W+N+S)
		search_button=create_image_button(Menu,"./.TexFlasher/search.png",40,40)
		search_button.configure(border=bordersize,command=search_flashcard)
		#print search_button['cursor']
		search_button.grid(row=1,column=2,sticky=N+E+W,columnspan=2)		
		v = IntVar()
		check = Checkbutton(Menu, text="search content", variable=v)
    		check.var = v
		check.grid(row=1,column=2,sticky=S+E+W,columnspan=2)
		#savebutton
		image_path="./.TexFlasher/upload.png"	
		if checkIfNeedToSave( saveString ):
			image_path="./.TexFlasher/upload_now.png"	
		exec('save=create_image_button(Menu,"'+image_path+'",'+button_size+','+button_size+')')
		exec('save.configure(border='+str(bordersize)+',command=lambda:saveFiles(saveString))')
		exec('save.grid(row=1, column=4,sticky=W+N+S+E,columnspan=4)')	
		Label(Menu,height=1).grid(sticky=E+W,row=2,columnspan=10)
	else:
		create.grid(row=row_start+1,columnspan=8)
	#footer
	Label(top,font=("Helvetica",8),text="Copyright (c) 2012: Can Oezmen, Axel Pfeiffer").grid(row=3,columnspan=8,sticky=S)
	mainloop()



##################################################################### Main ###############################################################################

user=commands.getoutput("echo $USER")
if( len(sys.argv) > 2 ):
	user=sys.argv[2]

version="TexFlasher unstable build"
top = Tk()

WIDTH=800
HEIGHT=int(WIDTH*0.6) +160

BD=2


top.bind("<Escape>", lambda e: top.quit()) # quits texflasher if esc is pressed



iconbitmapLocation = "@./.TexFlasher/icon2.xbm"
top.iconbitmap(iconbitmapLocation)
top.iconmask(iconbitmapLocation)

top.geometry(str(int(WIDTH*1.005))+"x"+str(HEIGHT))

menu()