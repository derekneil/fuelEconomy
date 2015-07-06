from pyquery import PyQuery as pq
from pandas import *
import re
from multiprocessing import Pool
from operator import is_not
from functools import partial

DEBUG = 1

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


nationalities = {
				14:'Australia',
				29:'Brazil',
				36:'Canada',
				46:'China',
				86:'Greece',
				99:'Ireland',
				152:'Mexico',
				153:'Maylasia',
				162:'Norway',
				166:'New Zealand',
				179:'Portugal',
				210:'Thailand',
				217:'Turkey',
				220:'Taiwan',
				222:'Ukraine',
				224:'United Kingdom',
				226:'United States',
				241:'South Africa',
				}

epaRE = re.compile('(d+)/(d+) mpg',flags=re.IGNORECASE)
curbWeightRE = re.compile('(d+) lbs\.',flags=re.IGNORECASE)
horespowerRE = re.compile('(d+) hp @',flags=re.IGNORECASE)	
def api(make, model, year):
	model = model.strip().replace(" ", "-")
	
	epa = ['','']
	type = ''
	curbWeight = ''
	horespower = ''
	
	try:
		modelFeatures = pq(url="http://www.edmunds.com/"+make+"/"+model+"/"+year+"/features-specs/")
		for feature in modelFeatures(".feature-spec .items td").items():
	# 		if DEBUG: print 
	# 		if DEBUG: print feature.html()
			label = feature("label").text()
	# 		if DEBUG: print 'label',label
			
			if "EPA MILEAGE EST. (CTY/HWY)" in label:
				epa = feature("span").text()
				if DEBUG: print 'found epa',epa,epaRE.findall(epa)
				epa = epaRE.findall(epa)
			elif "CAR TYPE" in label:
				type = feature("span").text().strip()
				if DEBUG: print 'found type',type
			elif "CURB WEIGHT" in label:
				curbWeight = feature("span").text()
				if DEBUG: print 'found curb weight',curbWeight,curbWeightRE.findall(curbWeight)
				curbWeight = curbWeightRE.findall(curbWeight)
			elif "HORSEPOWER" in label:
				horsepower = feature("span").text()
				if DEBUG: print 'found horsepower',horsepower,horsepowerRE.findall(horsepower)
				horespower = horsepowerRE.findall(horsepower)
			
		print epa[0], epa[1], type, curbWeight, horespower 
	except:
		if DEBUG: print '\n\tedmunds api error'
	
	return epa[0], epa[1], type, curbWeight, horespower 
	
def scrape(url, destination):
	
	#get listing of all car models
	try:
		makeModelListing = pq(url='http://www.fuelly.com/car')
	except:
		if DEBUG: print '\n\tHTTP 404'
		return
	
	makeRE = re.compile('http://www.fuelly.com/car/(.*)/',flags=re.IGNORECASE)
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
 	makeModelsDF = makeModelsDF.sort(columns='count',ascending=False)
 	
 	#just do small test set
 	if DEBUG: makeModelsDF = makeModelsDF.head()
	
	def getMakeModelInfo(makeModel):
		try:
			makeName = makeModel['makeName']
			modelName = makeModel['modelName']
			link = makeModel['link']
			if DEBUG: print link
			if DEBUG: print makeName
			if DEBUG: print modelName
			modelPage = pq(url=link)
			for modelYear in modelPage('.model-year-summary').items():
				if DEBUG: print 
				if DEBUG: print modelYear.html()
				year         = modelYear('.summary-year').text()
				yearAvg      = modelYear('.summary-avg').text()
# 				yearOwners   = modelYear('.summary-total').text()
# 				yearFuelups  = modelYear('.summary-fuelups').text()
# 				yearMiles    = modelYear('.summary-miles').text()
				yearLink     = modelYear('.summary-view-all-link a').attr('href')
				#get model info
				
				epaCity, epaHwy, typ, weight, hp = api(makeName, modelName, year)
	
				#store data for this make model and year
				thisMakeModelInfo = {'year':year, 'make':makeName, 'model':modelName, 
									'type':type, 'weight':weight, 'horsepower':hp,
									'avg':yearAvg, 'fuelups':yearFuelups, 'link':yearLink}
				
				ownerMakeModelInfo = []
				
				modelYearListing = pq(yearLink)
				
				# TODO need to add pagination support here!!!!!!!
				
				for car in modelYearListing('.browse-by-vehicle-display').items():
					if DEBUG: print 
					if DEBUG: print car.html()
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
					ownerLink = car('.browse-by-vehicle-display').attr('data-clickable')
					nationality = car('.browse-details p:last a img').attr('src')
					nationality = nationalities.get(nationality, nationality)
					
					# get detail location from user page
					ownerPage = pq(ownerLink)
					
					# get engine size, fuel ups, avg mpg
					engineSize    = ownerPage('.vehicle-info .extended_desc small').text()
					location      = ownerPage('.vehicle-info p:last .show .text-muted').text()
					avg           = ownerPage('.basic-stats.average-mileage .stat-item strong').text()
					avgCostGallon = ownerPage('.vehicle-costs-list-item.js-average-cost .js-cost-analysis-value').text()
# 					avgCostFillup = ownerPage('.vehicle-costs-list-item.js-average-fillup .js-cost-analysis-value').text()
# 					avgCostMile   = ownerPage('.vehicle-costs-list-item.js-average-mile .js-cost-analysis-value').text()
					fuelUpsCount  = ownerPage('.total-fuelups-count').text()
# 					miles         = ownerPage('.total-miles-digits li').text().replace(' ','')
	
					#store data for this user vehidle entry
					ownerMakeModelInfo.append({'year':year, 'make':makeName, 'model':modelName, 
											'type':type, 'weight':weight, 'horsepower':hp,
											'avg':avg, 'fuelups':fuelUpsCount, 'avgCostGallon':avgCostGallon,
											'engineSize':engineSize, 'nationality':nationality, 'location':location})
					
				return thisMakeModelInfo, ownerMakeModelInfo
	
 		except:
 			return None
 		
 	pool = Pool(processes=4)
 	makeModelInfo, ownerModelInfo = pool.map(getMakeModelInfo, makeModels)
 	if DEBUG: print
 	if DEBUG: print 'makeModelInfo', len(makeModelInfo)
 	if DEBUG: print 'ownerModelInfo', len(ownerModelInfo)
 	makeModelInfo  = filter(partial(is_not, None), makeModelInfo)
 	ownerModelInfo = filter(partial(is_not, None), ownerModelInfo)
 	
 	if DEBUG: print 'ownerModelInfo missing nationalities', unique(ownerModelInfo['nationality'])
 	
 	makeModelInfo = DataFrame(makeModelInfo)
	if DEBUG: print
	if DEBUG: print makeModelInfo
	makeModelInfo.to_csv(destination+'make-model.csv')
	if DEBUG: print '\nSaved make-model dataframe to csv'
 	
 	ownerModelInfo = DataFrame(ownerModelInfo)
	if DEBUG: print
	if DEBUG: print ownerModelInfo
	ownerModelInfo.to_csv(destination+'owner-model.csv')
	if DEBUG: print '\nSaved owner-model dataframe to csv'
				
# -----------------------------------------------------------------------------

url = 'http://www.fuelly.com/car'
destination = 'fuelly-car-data'

print '\Starting...'

scrape(url, destination)

print '\nDone'
