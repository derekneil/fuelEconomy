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

nationalities = {
	1:'Andorra',
	2:'United Arab Emirates',
	3:'Afghanistan',
	4:'Antigua and Barbuda',
	5:'Anguilla',
	6:'Albania',
	7:'Armenia',
	8:'Netherlands Antilles',
	9:'Angola',
	10:'Antarctica',
	11:'Argentina',
	12:'American Samoa',
	13:'Austria',
	14:'Australia',
	15:'Aruba',
	16:'Azerbaijan',
	17:'Bosnia and Herzegovina',
	18:'Barbados',
	19:'Bangladesh',
	20:'Belgium',
	21:'Burkina Faso',
	22:'Bulgaria',
	23:'Bahrain',
	24:'Burundi',
	25:'Benin',
	26:'Bermuda',
	27:'Brunei',
	28:'Bolivia',
	29:'Brazil',
	30:'Bahamas',
	31:'Bhutan',
	33:'Botswana',
	34:'Belarus',
	35:'Belize',
	36:'Canada',
	37:'Cocos Islands',
	38:'Congo',
	39:'Central African Republic',
	40:'Brazzaville',
	41:'Switzerland',
	42:'Ivory Coast',
	43:'Cook Islands',
	44:'Chile',
	45:'Cameroon',
	46:'China',
	47:'Colombia',
	48:'Costa Rica',
	49:'Cuba',
	50:'Cape Verde',
	51:'Christmas Island',
	52:'Cyprus',
	53:'Czech Republic',
	54:'Germany',
	55:'Djibouti',
	56:'Denmark',
	57:'Dominica',
	58:'Dominican Republic',
	59:'Algeria',
	60:'Ecuador',
	61:'Estonia',
	62:'Egypt',
	63:'Western Sahara',
	64:'Eritrea',
	65:'Spain',
	66:'Ethiopia',
	67:'Finland',
	68:'Fiji',
	69:'Falkland Islands',
	71:'Faroe Islands',
	72:'France',
	74:'Gabon',
	75:'Grenada',
	76:'Georgia',
	77:'Gviana',
	78:'Guernsey',
	79:'Ghana',
	80:'Gibraltar',
	81:'Greenland',
	82:'Gambia',
	83:'Guinea',
	84:'Equatorial Guinea',
	86:'Greece',
	88:'Guatemala',
	89:'Guam',
	90:'Guinea Bissau',
	91:'Guyana',
	92:'Hong Kong',
	94:'Honduras',
	95:'Croatia',
	96:'Haiti',
	97:'Hungary',
	98:'Indonesia',
	99:'Ireland',
	100:'Israel',
	101:'Isle of Man',
	102:'India',
	104:'Iraq',
	105:'Iran',
	106:'Iceland',
	107:'Italy',
	108:'Jersey',
	109:'Jamaica',
	110:'Jordan',
	111:'Japan',
	112:'Kenya',
	113:'Kyrgyzstan',
	114:'Cambodia',
	115:'Kiribati',
	116:'Comoros',
	117:'Saint Kitts and Nevis',
	119:'South Korea',
	120:'Kuwait',
	121:'Cayman Islands',
	122:'Kazakhstan',
	123:'Laos',
	124:'Lebanon',
	125:'Saint Lucia',
	126:'Liechtenstein',
	127:'Sri Lanka',
	128:'Liberia',
	129:'Lesotho',
	130:'Lithuania',
	131:'Luxembourg',
	132:'Latvia',
	133:'Libya',
	134:'Morocco',
	135:'Monaco',
	136:'Moldova',
	137:'Madagascar',
	138:'Marshall Islands',
	139:'Macedonia',
	140:'Mali',
	141:'Myanmar',
	142:'Mongolia',
	143:'Macau',
	144:'Northern Mariana Islands',
	145:'Martinique',
	146:'Mauritania',
	147:'Montserrat',
	148:'Malta',
	149:'Mauritius',
	150:'Maldives',
	151:'Malawi',
	152:'Mexico',
	153:'Maylasia',
	154:'Mozambique',
	155:'Namibia',
	156:'New Caledonia',
	157:'Niger',
	158:'Norfolk Island',
	159:'Nigeria',
	160:'Nicaragua',
	161:'Netherlands',
	162:'Norway',
	163:'Nepal',
	164:'Nauru',
	165:'Niue',
	166:'New Zealand',
	167:'Oman',
	168:'Panama',
	169:'Peru',
	170:'French Polynesia',
	171:'Papua New Guinea',
	172:'Philippines',
	173:'Pakistan',
	174:'Poland',
	175:'Saint Pierre and Miquelon ',
	176:'Pitcairn Islands',
	177:'Puerto Rico',
	178:'Palestine',
	179:'Portugal',
	180:'Palau',
	181:'Paraguay',
	182:'Qatar',
	184:'Romania',
	185:'Russia',
	186:'Rwanda',
	187:'Saudi Arabia',
	188:'Solomon Islands',
	189:'Seychelles',
	190:'Sudan',
	191:'Sweden',
	192:'Singapore',
	193:'Saint Helena',
	194:'Slovenia',
	195:'Norway',
	196:'Slovakia',
	197:'Sierra Leone',
	198:'San Marino',
	199:'Senegal',
	200:'Somalia',
	201:'Suriname',
	202:'Sao Tome and Principe',
	203:'El Salvador',
	204:'Syria',
	205:'Swaziland',
	206:'Turks and Caicos Islands',
	207:'Chad',
	209:'Togo',
	210:'Thailand',
	211:'Tajikistan',
	212:'Tokelau',
	213:'Turkmenistan',
	214:'Tunisia',
	215:'Tonga',
	216:'Timor Leste',
	217:'Turkey',
	218:'Trinidad and Tobago',
	219:'Tuvalu',
	220:'Taiwan',
	221:'Tanzania',
	222:'Ukraine',
	223:'Uganda ',
	224:'United Kingdom',
	226:'United States',
	227:'Uruguay',
	228:'Uzbekistan',
	230:'Saint Vincent and The Grenadines ',
	231:'Venezuela',
	232:'British Virgin Islands',
	233:'United States Virgin Islands',
	234:'Vietnam',
	235:'Vanuatu',
	236:'Wallis and Futuna',
	237:'Samoa',
	238:'Yemen',
	241:'South Africa',
	242:'Zambia',
	243:'Zimbabwe',
	244:'Serbia',
	245:'Montenegro'
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
			
			year         = modelYear('.summary-year').text().strip()
			yearAvg      = modelYear('.summary-avg').text().split(' ')[0]
			yearOwners   = modelYear('.summary-total').text().strip().split(' ')[0].replace(",", "")
			yearFuelups  = modelYear('.summary-fuelups').text().strip().split(' ')[0].replace(",", "")
			yearMiles    = modelYear('.summary-miles').text().strip().split(' ')[0].replace(",", "")
			yearLink     = modelYear('.summary-view-all-link a').attr('href')
			
			#get model specific info from edmunds api
			type, weight, hp = api(makeName, modelName, year)

			modelYearListing = pq(yearLink)
			
			pages = [yearLink]
			for link in modelYearListing('.pagination li a').items():
				pages.append(link.attr('href'))
				
			for link in pages:
				modelYearListing = pq(link)
			
				for ownerCar in modelYearListing('.browse-by-vehicle-display').items():
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
					ownerModelInfo.append(ownerModel)
					
			#save this owner-make-model-year info
			ownerMakeModelYear = DataFrame(ownerModelInfo)
	 		ownerMakeModelYear.to_csv(destination+'-owner-makeModel-'+makeName+'-'+modelName+'-info-utf8-.csv',encoding='utf-8')
	 		print '\tsaved utf8', makeName, modelName, year
	 		
	 		if DEBUG: print '\tnationalities:', unique(ownerMakeModelYear['country'])
				
		return ownerModelInfo
	
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
 	makeModelsDF = makeModelsDF[makeModelsDF['count']<3400]
	makeModelsDF = makeModelsDF[makeModelsDF['count']>600]
 	
 	ownerModelInfo = []
 	for index, makeModel in makeModelsDF.iterrows():
 		owner = getMakeModelInfo(makeModel)
 		if model is not None:
	 		ownerModelInfo.extend(owner)
	 		
	 		try:
			 	df = DataFrame(ownerModelInfo)
				df.to_csv(destination+'-owner-model-info-inprogress.csv', encoding='utf-8')
				print 'Saved in progress owner-model dataframe to csv'
			except:
				print 'error saving running totals', makeModel['makeName'], makeModel['modelName']
	 	
 	ownerModelInfo = DataFrame(ownerModelInfo)
	ownerModelInfo.to_csv(destination+'-owner-model-info.csv', encoding='utf-8')
	print '\nSaved owner-model dataframe to csv'
 	
 	if DEBUG: print 'ownerModelInfo missing nationalities', unique(ownerModelInfo['country'])
				
# -----------------------------------------------------------------------------

print '\Starting...'

scrape()

print '\nDone'
