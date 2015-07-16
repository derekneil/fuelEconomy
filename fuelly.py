from pyquery import PyQuery as pq
from pandas import *
import re
from multiprocessing import Pool
from operator import is_not
from functools import partial

DEBUG = 1
url = 'http://www.fuelly.com/car'
destination = 'fuelly-car-data'

#Sample model listing
'''
<div class="row">
	<div class="col-sm-12 col-md-12">			
						<h4 class="make-header"><a class="make-header-link" href="http://www.fuelly.com/car/abarth">Abarth</a></h4>
			<ul class="models-list">
								<li><a href="http://www.fuelly.com/car/abarth/1000">1000</a> (1)</li>
								<li><a href="http://www.fuelly.com/car/abarth/500">500</a> (69)</li>
								<li><a href="http://www.fuelly.com/car/abarth/750">750</a> (1)</li>
								<li><a href="http://www.fuelly.com/car/abarth/assetto">Assetto</a> (1)</li>
								<li><a href="http://www.fuelly.com/car/abarth/gnasher">Gnasher</a> (1)</li>
								<li><a href="http://www.fuelly.com/car/abarth/grande_punto">Grande Punto</a> (3)</li>
								<li><a href="http://www.fuelly.com/car/abarth/punto_evo">Punto Evo</a> (5)</li>
								<li><a href="http://www.fuelly.com/car/abarth/punto_supersport">Punto Supersport</a> (1)</li>
							</ul>
						<h4 class="make-header"><a class="make-header-link" href="http://www.fuelly.com/car/ac">AC</a></h4>
			<ul class="models-list">
								<li><a href="http://www.fuelly.com/car/ac/427">427</a> (3)</li>
							</ul>
						<h4 class="make-header"><a class="make-header-link" href="http://www.fuelly.com/car/acura">Acura</a></h4>
			<ul class="models-list">
								<li><a href="http://www.fuelly.com/car/acura/cl">CL</a> (56)</li>
								<li><a href="http://www.fuelly.com/car/acura/csx">CSX</a> (40)</li>
								<li><a href="http://www.fuelly.com/car/acura/el">EL</a> (81)</li>

'''

def safeInt(s):
	try:
		s = s.replace(',','')
		s = s.split('.')[0]
		i = int(s)
		return i
	except ValueError:
		return s

nationalities = {
	14:'Australia',
	29:'Brazil',
	36:'Canada',
	46:'China',
	67:'Finland',
	86:'Greece',
	99:'Ireland',
	152:'Mexico',
	153:'Maylasia',
	162:'Norway',
	166:'New Zealand',
	179:'Portugal',
	191:'Sweden',
	210:'Thailand',
	217:'Turkey',
	220:'Taiwan',
	222:'Ukraine',
	224:'United Kingdom',
	226:'United States',
	241:'South Africa'
	}

curbWeightRE = re.compile('(\d+) lbs',flags=re.IGNORECASE)
horsepowerRE = re.compile('(\d+).*hp.*',flags=re.IGNORECASE)	
def api(make, model, year):
	model = model.strip().replace(" ", "-")
	
	type = ''
	curbWeight = ''
	horsepower = ''
	url="http://www.edmunds.com/"+make+"/"+model+"/"+year+"/features-specs/"
	
	try:
		if DEBUG: print '\tedmunds api call to',url
		modelFeatures = pq(url=url)
		
		for highlight in modelFeatures("#highlights-pod .data-table li").items():
# 			if DEBUG: print 
# 	 		if DEBUG: print highlight.html()
			span = highlight("span").text()
# 			if DEBUG: print 'span:',span
			
			if "CAR TYPE" in span:
				type = highlight("em").text().strip().upper()
# 				if DEBUG: print 'found type',type
		
		for feature in modelFeatures(".feature-spec .items td").items():
# 	 		if DEBUG: print 
# 	 		if DEBUG: print feature.html()
			label = feature("label").text()
# 	 		if DEBUG: print 'label:',label
			
			if "CURB WEIGHT" in label:
				curbWeight = feature("span").text()
# 				if DEBUG: print 'found curb weight',curbWeight,curbWeightRE.findall(curbWeight)
				curbWeight = curbWeightRE.findall(curbWeight)[0]
			elif "HORSEPOWER" in label:
				horsepower = feature("span").text()
# 				if DEBUG: print 'found horsepower',horsepower,horsepowerRE.findall(horsepower)
				horsepower = horsepowerRE.findall(horsepower)[0]
			
		if DEBUG: print '\ttype:',type, 'curbWeight:',curbWeight, 'horespower',horsepower 
	except:
		if DEBUG: print '\tedmunds api error'
	
	return type, curbWeight, horsepower 

engineRE = re.compile('(\d\.*\d*L).*[FLEX|GAS|DIESEL|CNG]',flags=re.IGNORECASE)
fuelRE = re.compile('(FLEX|GAS|DIESEL|CNG)',flags=re.IGNORECASE)
transRE = re.compile('(Automatic.* \d|Standard \d|Automatic CVT)',flags=re.IGNORECASE)
countryRE     = re.compile('/(\d+)\..*',flags=re.IGNORECASE)
commaDigitsRE = re.compile('(\d*,*\d+) Fuel-ups',flags=re.IGNORECASE)
decimalRE     = re.compile('(\d*\.*\d+)',flags=re.IGNORECASE)
def getMakeModelInfo(makeModel):
# 		try:
		makeName = makeModel['makeName']
		modelName = makeModel['modelName']
		link = makeModel['link']
		if DEBUG: print link
		print '\tretrieving:',makeName, modelName
			
		makeModelInfo  = []
		ownerModelInfo = []
		
		modelPage = pq(url=link)
		for modelYear in modelPage('.model-year-summary').items():
# 				if DEBUG: print 
# 				if DEBUG: print modelYear.html()
			
			year         = modelYear('.summary-year').text().strip()
			yearAvg      = modelYear('.summary-avg').text().split(' ')[0]
			yearOwners   = modelYear('.summary-total').text().strip().split(' ')[0].replace(",", "")
			yearFuelups  = modelYear('.summary-fuelups').text().strip().split(' ')[0].replace(",", "")
			yearMiles    = modelYear('.summary-miles').text().strip().split(' ')[0].replace(",", "")
			yearLink     = modelYear('.summary-view-all-link a').attr('href')
			
# 				if yearFuelups < threshold and yearMiles < threshold: return None, None
			
			#get model specific info from edmunds api
			type, weight, hp = api(makeName, modelName, year)

			#store data for this make model and year
			makeModelInfo.append({'year':year, 'make':makeName, 'model':modelName, 
								'type':type, 'weight':weight, 'horsepower':hp,
								'avgMpg':yearAvg, 'fuelups':yearFuelups, 
								'owners':yearOwners,'miles':yearMiles, 'link':yearLink})
			
			modelYearListing = pq(yearLink)
			
			pages = [yearLink]
			for link in modelYearListing('.pagination li a').items():
				pages.append(link.attr('href'))
				
			for link in pages:
				modelYearListing = pq(link)
			
				for ownerCar in modelYearListing('.browse-by-vehicle-display').items():
# 						if DEBUG: print 
# 						if DEBUG: print ownerCar.html()
					
					#sample model year item
					'''
					<ul class="browse-by-vehicle-display" data-clickable="http://www.fuelly.com/car/abarth/500/2014/deathstalker/285920" style="cursor: pointer;">
						<li class="browse-image car" style="background-image:url('/photos/000099/r1/15397b5e37028a4.33780631.jpg')">	 </li>
						<li class="browse-details">
							<h4>Bianca</h4>
							<p><strong>2014 Abarth 500  GAS L4 <br><span class="date">Added May 2014</span> - 23 <span>Fuel-ups</span></strong></p>
							<p>Property of <a href="http://www.fuelly.com/driver/deathstalker" class="profile-link"><span class="fy-icon-avatar"></span> Deathstalker <img src="/img/badges/countries/226.gif"></a></p>
						</li>
						<li class="browse-performance ">
							<div class="vertical-stat">	
							 
								<strong>38.2</strong> <em>Avg MPG</em>
							</div>
						</li>
					</ul>
					'''
					ownerLink = ownerCar('.browse-by-vehicle-display').attr('data-clickable')
					country = ownerCar('.browse-details p:last a img').attr('src')
					country = countryRE.findall(country)[0]
					country = safeInt(country)
					country = nationalities.get(country, country)
					
					# get detail location from user page
					ownerPage = pq(ownerLink)
					
					# get engine size, fuel ups, avg mpg
					engineAndTransmission = ownerPage('.vehicle-info .extended_desc small').text()
					
					engineSize = engineRE.findall(engineAndTransmission)
					if engineSize:
						engineSize = engineSize[0].strip()
						if "L" in engineSize: engineSize = engineSize.strip().replace('L','')
					else:
						engineSize = ''
					fuel = fuelRE.findall(engineAndTransmission)
					if fuel:
						fuel = fuel[0]
						if "DIESEL" in fuel: fuel = "D"
						elif "GAS" in fuel:  fuel = "X"
						elif "CNG" in fuel:  fuel = "N"
					else:
						fuel = ''
					
					transmission = transRE.findall(engineAndTransmission)
					if transmission:
						transmission = transmission[0]
						if "Automatic CVT" in transmission: transmission = "AV"
						elif "Standard" in transmission:    transmission = "M"+transmission.strip().split(' ')[1]
						elif "Automatic" in transmission:   transmission = "A"+transmission.strip().split(' ')[-1]
					else:
						transmission = ''
					
					location      = ownerPage('.vehicle-info p:last .show .text-muted').text().strip()
					avgMpg        = ownerPage('.basic-stats.average-mileage .stat-item strong').text()
					avgCostGallon = ownerPage('.vehicle-costs-list-item.js-average-cost .js-cost-analysis-value').text()
# 					avgCostFillup = ownerPage('.vehicle-costs-list-item.js-average-fillup .js-cost-analysis-value').text()
# 					avgCostMile   = ownerPage('.vehicle-costs-list-item.js-average-mile .js-cost-analysis-value').text()
					fuelUpsCount  = ownerPage('.total-fuelups-count').text().strip().replace(',','')
					
					avgCostGallon = decimalRE.findall(avgCostGallon)
					if avgCostGallon:
						avgCostGallon = float(avgCostGallon[0])
						if avgCostGallon > 10:
							if DEBUG: print '\t\tavgCostGallon really high',avgCostGallon,'check link',ownerLink
							
 					miles         = ownerPage('.total-miles-digits li').text().replace(' ','')
 					miles         = safeInt(miles)
	
					#store data for this user vehicle entry
					ownerModel = {'year':year, 'make':makeName, 'model':modelName, 
								'class':type, 'fuel':fuel, 'weight':weight, 'horsepower':hp,
								'engineSize':engineSize, 'transmission':transmission,
								'avgMpg':avgMpg, 'country':country, 'location':location,
								'fuelups':fuelUpsCount, 'avgCostGallon':avgCostGallon, 
								'miles':miles, 'link':ownerLink }
# 					if DEBUG: print ownerModel
					ownerModelInfo.append(ownerModel)
					
			#save this owner-make-model-year info
			ownerMakeModelYear = DataFrame(ownerModelInfo)
	 		ownerMakeModelYear.to_csv(destination+'-owner-makeModel-'+makeName+'-'+modelName+'-info-utf8-.csv',encoding='utf-8')
	 		print '\tsaved utf8', makeName, modelName, year
				
		return makeModelInfo, ownerModelInfo
# 	
#  		except:
#  			print 'error in getMakeModelInfo'
#  			return None, None
	
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
 		if DEBUG: print model.html()
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
 	makeModelsDF = makeModelsDF.sort(columns='count',ascending=True)
 	
 	if DEBUG: print
 	makeModelsDF.to_csv(destination+'-make-models-utf8.csv', encoding='utf-8')
	makeModelsDF = makeModelsDF[makeModelsDF['count']>500]
	if DEBUG: makeModelsDF = makeModelsDF.head()
 	
 	makeModelInfo = []
 	ownerModelInfo = []
 	
 	#resume where we left off scrapping fuelly.com
 	progressFilename = 'fuellyProgress.txt'
	f = open(progressFilename, 'r+')
	lastRecord = safeInt(f.readline())
	f.close()
 	
 	i = -1
 	for index, makeModel in makeModelsDF.iterrows():
 		i += 1
 		if (i < lastRecord):
 			continue
 		
 		model, owner = getMakeModelInfo(makeModel)
 		
 		if model is not None:
 			try:
		 		df1 = DataFrame(model)
		 		df2 = DataFrame(owner)
	 			df1.to_csv(destination+'-make-model-info-utf8-'+`i`+'.csv', encoding='utf-8')
		 		df2.to_csv(destination+'-owner-model-info-utf8-'+`i`+'.csv',encoding='utf-8')
		 		print 'saved model info utf8'
 			except:
 				print 'error csv WITH utf-8 encoding ',makeModel['makeName'], makeModel['modelName']
 				
	 		makeModelInfo.extend(model)
	 		ownerModelInfo.extend(owner)
	 		
	 		try:
			 	df3 = DataFrame(makeModelInfo)
				df3.to_csv(destination+'-make-model-info-inprogress.csv', encoding='utf-8')
				print 'Saved make-model dataframe to csv'
			 	
			 	df4 = DataFrame(ownerModelInfo)
				df4.to_csv(destination+'-owner-model-info-inprogress.csv', encoding='utf-8')
				print 'Saved owner-model dataframe to csv'
			except:
				print 'error saving running totals', makeModel['makeName'], makeModel['modelName']
	 	
	 	#remember where we left off scrapping fuelly.com
	 	f = open(progressFilename, 'w+')
		f.write('%d' % i)
		f.close()
	 	
 	if DEBUG: print
 	if DEBUG: print 'makeModelInfo', len(makeModelInfo)
 	if DEBUG: print 'ownerModelInfo', len(ownerModelInfo)
 	
 	makeModelInfo = DataFrame(makeModelInfo)
	if DEBUG: print
	if DEBUG: print makeModelInfo
	makeModelInfo.to_csv(destination+'-make-model-info.csv', encoding='utf-8')
	print '\nSaved make-model dataframe to csv'
 	
 	ownerModelInfo = DataFrame(ownerModelInfo)
	if DEBUG: print
	if DEBUG: print ownerModelInfo
	ownerModelInfo.to_csv(destination+'-owner-model-info.csv', encoding='utf-8')
	print '\nSaved owner-model dataframe to csv'
 	
 	if DEBUG: print 'ownerModelInfo missing nationalities', unique(ownerModelInfo['country'])
				
# -----------------------------------------------------------------------------

print '\Starting...'

scrape()

print '\nDone'
