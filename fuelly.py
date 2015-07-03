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
				
				226:'United States'
				
				}

epaRE = re.compile('(d+)/(d+) mpg',flags=re.IGNORECASE)
curbWeightRE = re.compile('(d+) lbs\.',flags=re.IGNORECASE)
horespowerRE = re.compile('(d+) hp @',flags=re.IGNORECASE)	
def api(make, model, year):
	model = model.strip().replace(" ", "-")
	
	epa = ['','']
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
			elif "CURB WEIGHT" in label:
				curbWeight = feature("span").text()
				if DEBUG: print 'found curb weight',curbWeight,curbWeightRE.findall(curbWeight)
				curbWeight = curbWeightRE.findall(curbWeight)
			elif "HORSEPOWER" in label:
				horsepower = feature("span").text()
				if DEBUG: print 'found horsepower',horsepower,horsepowerRE.findall(horsepower)
				horespower = horsepowerRE.findall(horsepower)
			
		print epa[0], epa[1], curbWeight, horespower 
	except:
		if DEBUG: print '\n\tedmunds api error'
	
	return epa[0], epa[1], curbWeight, horespower 
	
def scrape(url, destination):
	
	#get listing of all car models
	try:
		makeModelListing = pq(url='http://www.fuelly.com/car')
	except:
		if DEBUG: print '\n\tHTTP 404'
		return
	
	makeRE = re.compile('http://www.fuelly.com/car/(.*)/',flags=re.IGNORECASE)
	
	for model in makeModelListing(".models-list li").items():
		if DEBUG: print 
		if DEBUG: print model.html()
		link = pq(model)('a').attr('href')
		makeName = makeRE.findall(link)[0]
		modelName = pq(model)('a').text()

		if DEBUG: print link
		if DEBUG: print makeName
		if DEBUG: print modelName

		modelPage = pq(url=link)
		for modelYear in modelPage('.model-year-summary').items():
			if DEBUG: print 
			if DEBUG: print modelYear.html()
			year         = modelYear('.summary-year').text()
			yearAvg      = modelYear('.summary-avg').text()
			yearOwners   = modelYear('.summary-total').text()
			yearFuelups  = modelYear('.summary-fuelups').text()
			yearMiles    = modelYear('.summary-miles').text()
			yearLink     = modelYear('.summary-view-all-link a').attr('href')
			#add model info
			
			epaCity, epaHwy, weight, hp = api(makeName, modelName, year)

			#store data for this make model and year
			
			modelYearListing = pq(yearLink)
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
				
				# get detail location from user page
				ownerPage = pq(ownerLink)
				
				# get engine size, fuel ups, avg mpg
				engineSize    = ownerPage('.vehicle-info .extended_desc small').text()
				location      = ownerPage('.vehicle-info p:last .show .text-muted').text()
				avg           = ownerPage('.basic-stats.average-mileage .stat-item strong').text()
				avgCostGallon = ownerPage('.vehicle-costs-list-item.js-average-cost .js-cost-analysis-value').text()
				avgCostFillup = ownerPage('.vehicle-costs-list-item.js-average-fillup .js-cost-analysis-value').text()
				avgCostMile   = ownerPage('.vehicle-costs-list-item.js-average-mile .js-cost-analysis-value').text()
				fuelUpsCount  = ownerPage('.total-fuelups-count').text()
				miles         = ownerPage('.total-miles-digits li').text().replace(' ','')

				#store data for this user vehidle entry
				
# -----------------------------------------------------------------------------

url = 'http://www.fuelly.com/car'
destination = 'fuelly-car-data.csv'

print '\Starting...'

scrape(url, destination)

print '\nDone'
