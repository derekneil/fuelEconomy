from pyquery import PyQuery as pq
from pandas import *
import re
from multiprocessing import Pool
from operator import is_not
from functools import partial

DEBUG = 1
url = 'http://www.fuelly.com/car'
destination = 'fuelly-car-data'

def safeInt(s):
	try:
		s = s.replace(',','')
		s = s.split('.')[0]
		i = int(s)
		return i
	except ValueError:
		return s

curbWeightRE = re.compile('(\d+) lbs',flags=re.IGNORECASE)
horsepowerRE = re.compile('(\d+).*hp.*',flags=re.IGNORECASE)	
def api(make, model, year):
	model = model.strip().replace(" ", "-")
	
	type = ''
	curbWeight = ''
	horsepower = ''
	url="http://www.edmunds.com/"+make+"/"+model+"/"+year+"/features-specs/"
	
	try:
		if DEBUG: print '\t\tedmunds api call to',url
		modelFeatures = pq(url=url)
		
		for highlight in modelFeatures("#highlights-pod .data-table li").items():
			span = highlight("span").text()
			
			if "CAR TYPE" in span:
				type = highlight("em").text().strip().upper()
		
		for feature in modelFeatures(".feature-spec .items td").items():
			label = feature("label").text()
			
			if "CURB WEIGHT" in label:
				curbWeight = feature("span").text()
				curbWeight = curbWeightRE.findall(curbWeight)[0]
			elif "HORSEPOWER" in label:
				horsepower = feature("span").text()
				horsepower = horsepowerRE.findall(horsepower)[0]
			
		if DEBUG: print '\t\ttype:',type, 'curbWeight:',curbWeight, 'horespower',horsepower 
	except:
		if DEBUG: print '\t\tedmunds api error'
	
	return type, curbWeight, horsepower 

commaDigitsRE = re.compile('(\d*,*\d+) Fuel-ups',flags=re.IGNORECASE)
decimalRE     = re.compile('(\d*\.*\d+)',flags=re.IGNORECASE)
def getMakeModelInfo(makeModel):
	
	makeName = makeModel['makeName']
	modelName = makeModel['modelName']
	link = makeModel['link']
	if DEBUG: print link
	print '\tretrieving:',makeName, modelName
		
	makeModelInfo  = []
	
	modelPage = pq(url=link)
	for modelYear in modelPage('.model-year-summary').items():
		
		year         = modelYear('.summary-year').text().strip()
		yearAvg      = modelYear('.summary-avg').text().split(' ')[0]
		yearOwners   = modelYear('.summary-total').text().strip().split(' ')[0].replace(",", "")
		yearFuelups  = modelYear('.summary-fuelups').text().strip().split(' ')[0].replace(",", "")
		yearMiles    = modelYear('.summary-miles').text().strip().split(' ')[0].replace(",", "")
		yearLink     = modelYear('.summary-view-all-link a').attr('href')
		
		#get model specific info from edmunds api
		type, weight, hp = api(makeName, modelName, year)

		#store data for this make model and year
		makeModelInfo.append({'year':year, 'make':makeName, 'model':modelName, 
							'type':type, 'weight':weight, 'horsepower':hp,
							'avgMpg':yearAvg, 'fuelups':yearFuelups, 
							'owners':yearOwners,'miles':yearMiles, 'link':yearLink})
			
	return makeModelInfo
	
def scrape():
	
	#get listing of all car models
	try:
		makeModelListing = pq(url='http://www.fuelly.com/car')
	except:
		if DEBUG: print '\nHTTP 404'
		return
	
	makeRE  = re.compile('http://www.fuelly.com/car/(.*)/',flags=re.IGNORECASE)
	countRE = re.compile('</a> \((.*)\)',flags=re.IGNORECASE)
	
 	makeModels = []
 	for model in makeModelListing(".models-list li").items():
 		link = pq(model)('a').attr('href')
 		count = model.html()
 		count = countRE.findall(count)
 		try:
 	 		count = int(count[0])
 	 	except ValueError:
		 	count = 0
 		makeModels.append({'makeName':makeRE.findall(link)[0].lower(), 
						'modelName':pq(model)('a').text().lower(), 
						'link': link,
						'count':count})
 		
 	makeModelsDF = DataFrame(makeModels)
 	makeModelsDF = makeModelsDF.sort(columns='count',ascending=False)
	makeModelsDF = makeModelsDF[makeModelsDF['count']<600]
	makeModelsDF = makeModelsDF[makeModelsDF['count']>50]
 	
 	makeModelInfo  = []
 	for index, makeModel in makeModelsDF.iterrows():
 		model = getMakeModelInfo(makeModel)
 		if model is not None:
	 		makeModelInfo.extend(model)
	 		try:
			 	df = DataFrame(makeModelInfo)
				df.to_csv(destination+'-make-model-year-info-inprogress.csv', encoding='utf-8')
				print 'Saved make-model in progress dataframe to csv'
			 	
			except:
				print 'error saving running totals', makeModel['makeName'], makeModel['modelName']
	 	
 	makeModelInfo = DataFrame(makeModelInfo)
	makeModelInfo.to_csv(destination+'-make-model-year-info.csv', encoding='utf-8')
	print '\nSaved make-model dataframe to csv'
 	
# -----------------------------------------------------------------------------

print '\Starting...'

scrape()

print '\nDone'
