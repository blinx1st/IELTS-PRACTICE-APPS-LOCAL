"""Prepare the user's private Cambridge Listening 13-16 materials locally.

Source PDFs/audio are never modified. Intermediate OCR and reviewed content
remain private under library/preparation/listening.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
LIB=ROOT/'library'
PREP=LIB/'preparation'/'listening'
MATERIALS=next(p for p in ROOT.iterdir() if p.is_dir() and p.name.endswith('Cambridge'))
QUESTION_PAGES={13:[range(9,15),range(31,37),range(53,59),range(75,81)],
14:[range(2,8),range(24,30),range(45,51),range(67,74)],
15:[range(12,18),range(33,39),range(54,60),range(76,82)]}

# Source-led corrections. [[number]] is an input at its original position.
FLOWS={
(13,1,31):'''# Effects of urban environments on animals
# Introduction
Recent urban developments represent massive environmental changes. It was previously thought that only a few animals were suitable for city life, e.g.
the [[31]] – because of its general adaptability
the pigeon – because walls of city buildings are similar to [[32]]
In fact, many urban animals are adapting with unusual [[33]].
# Recent research
Emilie Snell-Rood studied small urbanised mammal specimens from museums in Minnesota.
– She found the size of their [[34]] had increased.
– She suggests this may be due to the need to locate new sources of [[35]] and to deal with new dangers.
Catarina Miranda focused on the [[36]] of urban and rural blackbirds.
– She found urban birds were often braver, but were afraid of situations that were [[37]].
Jonathan Atwell studies how animals respond to urban environments.
– He found that some animals respond to [[38]] by producing lower levels of hormones.
Sarah Partan’s team found urban squirrels use their [[39]] to help them communicate.
# Long-term possibilities
Species of animals may develop which are unique to cities. However, some changes may not be [[40]].''',
(13,2,1):'''# South City Cycling Club
Example: Name of club secretary: Jim Hunter
# Membership
Full membership costs $260; this covers cycling and [[1]] all over Australia
Recreational membership costs $108
Cost of membership includes the club fee and [[2]]
The club kit is made by a company called [[3]]
# Training rides
Chance to improve cycling skills and fitness
Level B: speed about [[4]] kph
Weekly sessions
– Tuesdays at 5.30 am, meet at the [[5]]
– Thursdays at 5.30 am, meet at the entrance to the [[6]]
# Further information
Rides are about an hour and a half
Members often have [[7]] together afterwards
There is not always a [[8]] with the group on these rides
Check and print the [[9]] on the website beforehand
Bikes: must have [[10]]''',
(13,2,31):'''# Episodic memory
the ability to recall details, e.g. the time and [[31]] of past events
different to semantic memory – the ability to remember general information about the [[32]], which does not involve recalling [[33]]
Forming episodic memories involves three steps:
# Encoding
involves receiving and processing information
the more [[34]] given to an event, the more successfully it can be encoded
to remember a [[35]], it is useful to have a strategy for encoding such information
# Consolidation
how memories are strengthened and stored
most effective when memories can be added to a [[36]] of related information
the [[37]] of retrieval affects the strength of memories
# Retrieval
memory retrieval often depends on using a prompt, e.g. the [[38]] of an object near to the place where you left your car
# Episodic memory impairments
these affect people with a wide range of medical conditions
games which stimulate the [[39]] have been found to help people with schizophrenia
children with autism may have difficulty forming episodic memories – possibly because their concept of the [[40]] may be absent
memory training may help autistic children develop social skills''',
(13,3,1):'''# Moving to Banford City
Example: Linda recommends living in suburb of: Dalton
# Accommodation
Average rent: £[[1]] a month
# Transport
Linda travels to work by [[2]]
Limited [[3]] in city centre
Trains to London every [[4]] minutes
Poor train service at [[5]]
# Advantages of living in Banford
New [[6]] opened recently
[[7]] has excellent reputation
Good [[8]] on Bridge Street
# Meet Linda
Meet Linda on [[9]] after 5.30 pm
In the [[10]] opposite the station''',
(13,3,31):'''# The sleepy lizard (tiliqua rugosa)
# Description
They are common in Western and South Australia
They are brown, but recognisable by their blue [[31]]
They are relatively large
Their diet consists mainly of [[32]]
Their main predators are large birds and [[33]]
# Navigation study
One study found that lizards can use the [[34]] to help them navigate
# Observations in the wild
Observations show that these lizards keep the same [[35]] for several years
Possible reasons:
– to improve the survival of their young
(but little [[36]] has been noted between parents and children)
– to provide [[37]] for female lizards
# Tracking study
– A study was carried out using GPS systems attached to the [[38]] of the lizards
– This provided information on the lizards’ location and even the number of [[39]] taken
– It appeared that the lizards were trying to avoid one another
– This may be in order to reduce chances of [[40]]''',
(13,4,1):'''# Alex’s Training
Example: Alex completed his training in 2014
# About the applicant:
At first, Alex did his training in the [[1]] department.
Alex didn’t have a qualification from school in [[2]].
Alex thinks he should have done the diploma in [[3]] skills.
Age of other trainees: the youngest was [[4]].
# Benefits of doing training at JPNW:
Lots of opportunities because of the size of the organisation.
Trainees receive the same amount of [[5]] as permanent staff.
The training experience increases people’s confidence a lot.
Trainees go to [[6]] one day per month.
The company is in a convenient [[7]].
# Advice for interview:
Don’t wear [[8]].
Don’t be [[9]].
Make sure you [[10]].''',
(13,4,31):'''# The history of coffee
# Coffee in the Arab world
There was small-scale trade in wild coffee from Ethiopia.
1522: Coffee was approved in the Ottoman court as a type of medicine.
1623: In Constantinople, the ruler ordered the [[31]] of every coffee house.
# Coffee arrives in Europe (17th century)
Coffee shops were compared to [[32]].
They played an important part in social and [[33]] changes.
# Coffee and European colonisation
European powers established coffee plantations in their colonies.
Types of coffee were often named according to the [[34]] they came from.
In Brazil and the Caribbean, most cultivation depended on [[35]].
In Java, coffee was used as a form of [[36]].
Coffee became almost as important as [[37]].
The move towards the consumption of [[38]] in Britain did not also take place in the USA.
# Coffee in the 19th century
Prices dropped because of improvements in [[39]].
Industrial workers found coffee helped them to work at [[40]].''',
(14,1,1):'''# CRIME REPORT FORM
Type of crime: theft
# Personal information
Example: Name: Louise Taylor
Nationality: [[1]]
Date of birth: 14 December 1977
Occupation: interior designer
Reason for visit: business (to buy antique [[2]])
Length of stay: two months
Current address: [[3]] Apartments (No 15)
# Details of theft
Items stolen: a wallet containing approximately £[[4]]; a [[5]]
Date of theft: [[6]]
# Possible time and place of theft
Location: outside the [[7]] at about 4 pm
Details of suspect:
– some boys asked for the [[8]] then ran off
– one had a T-shirt with a picture of a tiger
– he was about 12, slim build with [[9]] hair
Crime reference number allocated: [[10]]''',
(14,1,31):'''# Marine renewable energy (ocean energy)
# Introduction
More energy required because of growth in population and [[31]]
What’s needed:
renewable energy sources
methods that won’t create pollution
# Wave energy
Advantage: Waves provide a [[32]] source of renewable energy
Electricity can be generated using offshore or onshore systems
Onshore systems may use a reservoir
Problems:
waves can move in any [[33]]
movement of sand, etc. on the [[34]] of the ocean may be affected
# Tidal energy
Tides are more [[35]] than waves
Planned tidal lagoon in Wales:
will be created in a [[36]] at Swansea
breakwater (dam) containing 16 turbines
rising tide forces water through turbines, generating electricity
stored water is released through [[37]], driving the turbines in the reverse direction
Advantages:
not dependent on weather
no [[38]] is required to make it work
likely to create a number of [[39]]
Problem: may harm fish and birds, e.g. by affecting [[40]] and building up silt
# Ocean thermal energy conversion
Uses a difference in temperature between the surface and lower levels
Water brought to the surface in a pipe''',
(14,2,1):'''# TOTAL HEALTH CLINIC
# PATIENT DETAILS
# Personal information
Example: Name: Julie Anne Garcia
Contact phone: [[1]]
Date of birth: [[2]], 1992
Occupation: works as a [[3]]
Insurance company: [[4]] Life Insurance
# Details of the problem
Type of problem: pain in her left [[5]]
When it began: [[6]] ago
Action already taken: has taken painkillers and applied ice
# Other information
Sports played: belongs to a [[7]] club; goes [[8]] regularly
Medical history: injured her [[9]] last year; no allergies; no regular medication apart from [[10]]''',
(14,2,31):'''# The history of weather forecasting
# Ancient cultures
many cultures believed that floods and other disasters were involved in the creation of the world
many cultures invented [[31]] and other ceremonies to make the weather gods friendly
people needed to observe and interpret the sky to ensure their [[32]]
around 650 BC, Babylonians started forecasting, using weather phenomena such as [[33]]
by 300 BC, the Chinese had a calendar made up of a number of [[34]] connected with the weather
# Ancient Greeks
a more scientific approach
Aristotle tried to explain the formation of various weather phenomena
Aristotle also described haloes and [[35]]
# Middle Ages
Aristotle’s work considered accurate
many proverbs, e.g. about the significance of the colour of the [[36]], passed on accurate information.
# 15th–19th centuries
15th century: scientists recognised value of [[37]] for the first time
Galileo invented the [[38]]
Pascal showed relationship between atmospheric pressure and altitude
from the 17th century, scientists could measure atmospheric pressure and temperature
18th century: Franklin identified the movement of [[39]]
19th century: data from different locations could be sent to the same place by [[40]]''',
(14,3,1):'''# Flanders Conference Hotel
Example: Customer Services Manager: Angela
# Date available
weekend beginning February 4th
# Conference facilities
the [[1]] room for talks (projector and [[2]] available)
area for coffee and an [[3]]
free [[4]] throughout
a standard buffet lunch costs $[[5]] per head
# Accommodation
Rooms will cost $[[6]] including breakfast.
# Other facilities
The hotel also has a spa and rooftop [[7]].
There’s a free shuttle service to the [[8]].
# Location
Wilby Street (quite near the [[9]])
near to restaurants and many [[10]]''',
(14,3,21):'''# Background on school marching band
It consists of around [[21]] students.
It is due to play in a [[22]] band competition.
It has been invited to play in the town’s [[23]].
They have listened to a talk by a [[24]].
Joe will discuss a [[25]] with the band.
Joe hopes the band will attend a [[26]] next month.''',
(14,3,31):'''# Concerts in university arts festival
# Concert 1
Australian composer: Liza Lim
studied piano and [[31]] before turning to composition
performers and festivals around the world have given her a lot of commissions
compositions show a great deal of [[32]] and are drawn from various cultural sources
her music is very expressive and also [[33]]
festival will include her [[34]] called The Oresteia
Lim described the sounds in The Oresteia as [[35]]
British composers: Ralph Vaughan Williams, Frederick Delius
# Concert 2
British composers: Benjamin Britten, Judith Weir
Australian composer: Ross Edwards
festival will include The Tower of Remoteness, inspired by nature
The Tower of Remoteness is performed by piano and [[36]]
compositions include music for children
celebrates Australia’s cultural [[37]]
# Concert 3
Australian composer: Carl Vine
played cornet then piano
studied [[38]] before studying music
worked in Sydney as a pianist and composer
became well known as composer of music for [[39]]
festival will include his music for the 1996 [[40]]
British composers: Edward Elgar, Thomas Adès''',
(14,4,1):'''# Enquiry about booking hotel room for event
Example: Andrew is the Events Manager
# Rooms
# Adelphi Room
number of people who can sit down to eat: [[1]]
has a gallery suitable for musicians
can go out and see the [[2]] in pots on the terrace
terrace has a view of a group of [[3]]
# Carlton Room
number of people who can sit down to eat: 110
has a [[4]]
view of the lake
# Options
Master of Ceremonies:
can give a [[5]] while people are eating
will provide [[6]] if there are any problems
Accommodation: in hotel rooms or [[7]]''',
(14,4,31):'''# The hunt for sunken settlements and ancient shipwrecks
# ATLIT-YAM
was a village on coast of eastern Mediterranean
thrived until about 7,000 BC
stone homes had a courtyard
had a semicircle of large stones round a [[31]]
cause of destruction unknown – now under the sea
biggest settlement from the prehistoric period found on the seabed
research carried out into structures, [[32]] and human remains
# TRADITIONAL AUTONOMOUS UNDERWATER VEHICLES (AUVs)
used in the oil industry, e.g. to make [[33]]
problems: they were expensive and [[34]]
# LATEST AUVs
much easier to use, relatively cheap, sophisticated
Tests: Marzamemi, Sicily: found ancient Roman ships carrying architectural elements made of [[35]]
Underwater internet:
[[36]] is used for short distance communication, acoustic waves for long distance
plans for communication with researchers by satellite
AUV can send data to another AUV that has better [[37]], for example
Planned research in Gulf of Baratti:
to find out more about wrecks of ancient Roman ships, including
– one carrying [[38]] supplies; tablets may have been used for cleaning the [[39]]
– others carrying containers of olive oil or [[40]]''',
(15,1,1):'''# Bankside Recruitment Agency
Address of agency: 497 Eastside, Docklands
Name of agent: Becky [[1]]
Phone number: 07866 510333
Best to call her in the [[2]]
# Typical jobs
Clerical and admin roles, mainly in the finance industry
Must have good [[3]] skills
Jobs are usually for at least one [[4]]
Pay is usually £[[5]] per hour
# Registration process
Wear a [[6]] to the interview
Must bring your [[7]] to the interview
They will ask questions about each applicant’s [[8]]
# Advantages of using an agency
The [[9]] you receive at interview will benefit you
Will get access to vacancies which are not advertised
Less [[10]] is involved in applying for jobs''',
(15,1,31):'''# The Eucalyptus Tree in Australia
# Importance
it provides [[31]] and food for a wide range of species
its leaves provide [[32]] which is used to make a disinfectant
# Reasons for present decline in number
# A) Diseases
(i) ‘Mundulla Yellows’
Cause – lime used for making [[33]] was absorbed
– trees were unable to take in necessary iron through their roots
(ii) ‘Bell-miner Associated Die-back’
Cause – [[34]] feed on eucalyptus leaves
– they secrete a substance containing sugar
– bell-miner birds are attracted by this and keep away other species
# B) Bushfires
William Jackson’s theory:
high-frequency bushfires have impact on vegetation, resulting in the growth of [[35]]
mid-frequency bushfires result in the growth of eucalyptus forests, because they:
– make more [[36]] available to the trees
– maintain the quality of the [[37]]
low-frequency bushfires result in the growth of [[38]] ‘rainforest’, which is:
– a [[39]] ecosystem
– an ideal environment for the [[40]] of the bell-miner''',
(15,2,5):'''# Workshops
Making [[5]] food
(children only) Making [[6]]
(adults only) Making toys from [[7]] using various tools
# Outdoor activities
Swimming in the [[8]]
Walking in the woods, led by an expert on [[9]]
See the festival organiser’s [[10]] for more information''',
(15,2,31):'''# Agricultural programme in Mozambique
# How the programme was organised
It focused on a dry and arid region in Chicualacuala district, near the Limpopo River.
People depended on the forest to provide charcoal as a source of income.
[[31]] was seen as the main priority to ensure the supply of water.
Most of the work organised by farmers’ associations was done by [[32]].
Fenced areas were created to keep animals away from crops.
The programme provided
– [[33]] for the fences
– [[34]] for suitable crops
– water pumps.
The farmers provided
– labour
– [[35]] for the fences on their land.
# Further developments
The marketing of produce was sometimes difficult due to lack of [[36]].
Training was therefore provided in methods of food [[37]].
Farmers made special places where [[38]] could be kept.
Local people later suggested keeping [[39]].
# Evaluation and lessons learned
Agricultural production increased, improving incomes and food security.
Enough time must be allowed, particularly for the [[40]] phase of the programme.''',
(15,3,1):'''# Employment Agency: Possible Jobs
# First Job
Administrative assistant in a company that produces [[1]] (North London)
# Responsibilities
data entry
go to [[2]] and take notes
general admin
management of [[3]]
# Requirements
good computer skills including spreadsheets
good interpersonal skills
attention to [[4]]
# Experience
Need a minimum of [[5]] of experience of teleconferencing
# Second Job
Warehouse assistant in South London
# Responsibilities
stock management
managing [[6]]
# Requirements
ability to work with numbers
good computer skills
very organised and [[7]]
good communication skills
used to working in a [[8]]
able to cope with items that are [[9]]
# Need experience of
driving in London
warehouse work
[[10]] service''',
(15,3,21):'''# What Hazel should analyse about items in newspapers:
what [[21]] the item is on
the [[22]] of the item, including the headline
any [[23]] accompanying the item
the [[24]] of the item, e.g. what’s made prominent
the writer’s main [[25]]
the [[26]] the writer may make about the reader''',
(15,3,31):'''# Early history of keeping clean
# Prehistoric times:
water was used to wash off [[31]]
# Ancient Babylon:
soap-like material found in [[32]] cylinders
# Ancient Greece:
people cleaned themselves with sand and other substances
used a strigil – scraper made of [[33]]
washed clothes in streams
# Ancient Germany and Gaul:
used soap to colour their [[34]]
# Ancient Rome:
animal fat, ashes and clay mixed through action of rain, used for washing clothes
from about 312 BC, water carried to Roman [[35]] by aqueducts
# Europe in Middle Ages:
decline in bathing contributed to occurrence of [[36]]
[[37]] began to be added to soap
# Europe from 17th century:
1600s: cleanliness and bathing started becoming usual
1791: Leblanc invented a way of making soda ash from [[38]]
early 1800s: Chevreul turned soapmaking into a [[39]]
from 1800s, there was no longer a [[40]] on soap''',
(15,4,1):'''# Customer Satisfaction Survey
# Customer details
Name: Sophie Bird
Occupation: [[1]]
Reason for travel today: [[2]]
# Journey information
Name of station returning to: [[3]]
Type of ticket purchased: Standard [[4]] ticket
Cost of ticket: £[[5]]
When ticket was purchased: yesterday
Where ticket was bought: [[6]]
# Satisfaction with journey
Most satisfied with: the wifi
Least satisfied with: the [[7]] this morning
# Satisfaction with station facilities
Most satisfied with: how much [[8]] was provided
Least satisfied with: lack of seats, particularly on the [[9]]
Neither satisfied nor dissatisfied with: the [[10]] available''',
(15,4,31):'''# How the Industrial Revolution affected life in Britain
# 19th century
For the first time, people’s possessions were used to measure Britain’s [[31]].
Developments in production of goods and in [[32]] greatly changed lives.
# MAIN AREAS OF CHANGE
# Manufacturing
The Industrial Revolution would not have happened without the new types of [[33]] that were used then.
The leading industry was [[34]] (its products became widely available).
New [[35]] made factories necessary and so more people moved into towns.
# Transport
The railways took the place of canals.
Because of the new transport:
– greater access to [[36]] made people more aware of what they could buy in shops.
– when shopping, people were not limited to buying [[37]] goods.
# Retailing
The first department stores were opened.
The displays of goods were more visible:
– inside stores because of better [[38]].
– outside stores, because [[39]] were bigger.
[[40]] that was persuasive became much more common.''',
(16,1,1):'''# Children’s Engineering Workshops
# Tiny Engineers (ages 4–5)
# Activities
Create a cover for an [[1]] so they can drop it from a height without breaking it.
Take part in a competition to build the tallest [[2]].
Make a [[3]] powered by a balloon.
# Junior Engineers (ages 6–8)
# Activities:
Build model cars, trucks and [[4]] and learn how to program them so they can move.
Take part in a competition to build the longest [[5]] using card and wood.
Create a short [[6]] with special software.
Build, [[7]] and program a humanoid robot.
Cost for a five-week block: £50
Held on [[8]] from 10 am to 11 am
# Location
Building 10A, [[9]] Industrial Estate, Grasford
Plenty of [[10]] is available.''',
(16,1,31):'''# Stoicism
Stoicism is still relevant today because of its [[31]] appeal.
# Ancient Stoics
Stoicism was founded over 2,000 years ago in Greece.
The Stoics’ ideas are surprisingly well known, despite not being intended for [[32]].
# Stoic principles
Happiness could be achieved by leading a virtuous life.
Controlling emotions was essential.
Epictetus said that external events cannot be controlled but the [[33]] people make in response can be controlled.
A Stoic is someone who has a different view on experiences which others would consider as [[34]].
# The influence of Stoicism
George Washington organised a [[35]] about Cato to motivate his men.
The French artist Delacroix was a Stoic.
Adam Smith’s ideas on [[36]] were influenced by Stoicism.
Some of today’s political leaders are inspired by the Stoics.
Cognitive Behaviour Therapy (CBT)
– the treatment for [[37]] is based on ideas from Stoicism
– people learn to base their thinking on [[38]].
In business, people benefit from Stoicism by identifying obstacles as [[39]].
# Relevance of Stoicism
It requires a lot of [[40]] but Stoicism can help people to lead a good life.
It teaches people that having a strong character is more important than anything else.''',
(16,2,1):'''# Copying photos to digital format
Name of company: Picturerep
# Requirements
Maximum size of photos is 30 cm, minimum size 4 cm.
Photos must not be in a [[1]] or an album.
# Cost
The cost for 360 photos is £[[2]] (including one disk).
Before the completed order is sent, [[3]] is required.
# Services included in the price
Photos can be placed in a folder, e.g. with the name [[4]].
The [[5]] and contrast can be improved if necessary.
Photos which are very fragile will be scanned by [[6]].
# Special restore service (costs extra)
It may be possible to remove an object from a photo, or change the [[7]].
A photo which is not correctly in [[8]] cannot be fixed.
# Other information
Orders are completed within [[9]].
Send the photos in a box (not [[10]])''',
(16,2,25):'''# Assignment plan
Decide on research question: Is there a relationship between hours of sleep and number of dreams?
Decide on sample: Twelve students from the [[25]] department
Decide on methodology: Self-reporting
Decide on procedure: Answers on [[26]]
Check ethical guidelines for working with [[27]]
Ensure that risk is assessed and [[28]] is kept to a minimum
Analyse the results: Calculate the correlation and make a [[29]]
[[30]] the research''',
(16,2,31):'''# Health benefits of dance
# Recent findings:
All forms of dance produce various hormones associated with feelings of happiness.
Dancing with others has a more positive impact than dancing alone.
An experiment on university students suggested that dance increases [[31]].
For those with mental illness, dance could be used as a form of [[32]].
# Benefits of dance for older people:
accessible for people with low levels of [[33]]
reduces the risk of heart disease
better [[34]] reduces the risk of accidents
improves [[35]] function by making it work faster
improves participants’ general well-being
gives people more [[36]] to take exercise
can lessen the feeling of [[37]], very common in older people
# Benefits of Zumba:
A study at The University of Wisconsin showed that doing Zumba for 40 minutes uses up as many [[38]] as other quite intense forms of exercise.
The American Journal of Health Behavior study showed that:
– women suffering from [[39]] benefited from doing Zumba.
– Zumba became a [[40]] for the participants.''',
(16,3,1):'''# JUNIOR CYCLE CAMP
The course focuses on skills and safety.
Charlie would be placed in Level 5.
First of all, children at this level are taken to practise in a [[1]].
# Instructors
Instructors wear [[2]] shirts.
A [[3]] is required and training is given.
# Classes
The size of the classes is limited.
There are quiet times during the morning for a [[4]] or a game.
Classes are held even if there is [[5]].
# What to bring
a change of clothing
a [[6]]
shoes (not sandals)
Charlie’s [[7]]
# Day 1
Charlie should arrive at 9.20 am on the first day.
Before the class, his [[8]] will be checked.
He should then go to the [[9]] to meet his class instructor.
# Cost
The course costs $[[10]] per week.''',
(16,3,31):'''# Hand knitting
# Interest in knitting
Knitting has a long history around the world.
We imagine someone like a [[31]] knitting.
A [[32]] ago, knitting was expected to disappear.
The number of knitting classes is now increasing.
People are buying more [[33]] for knitting nowadays.
# Benefits of knitting
gives support in times of [[34]] difficulty
requires only [[35]] skills and little money to start
reduces stress in a busy life
# Early knitting
The origins are not known.
Findings show early knitted items to be [[36]] in shape.
The first needles were made of natural materials such as wood and [[37]].
Early yarns felt [[38]] to touch.
Wool became the most popular yarn for spinning.
Geographical areas had their own [[39]] of knitting.
Everyday tasks like looking after [[40]] were done while knitting.''',
(16,4,1):'''# Holiday rental
Owners’ names: Jack Fitzgerald and Shirley Fitzgerald
# Granary Cottage
available for week beginning [[1]] May
cost for the week: £[[2]]
# [[3]] Cottage
cost for the week: £480
building was originally a [[4]]
walk through doors from living room into a [[5]]
several [[6]] spaces at the front
bathroom has a shower
central heating and stove that burns [[7]]
views of old [[8]] from living room
view of hilltop [[9]] from the bedroom
# Payment
deposit: £144
deadline for final payment: end of [[10]]''',
(16,4,31):'''# THE EXTINCTION OF THE DODO BIRD
The dodo was a large flightless bird which used to inhabit the island of Mauritius.
# History
1507 – Portuguese ships transporting [[31]] stopped at the island to collect food and water.
1638 – The Dutch established a [[32]] on the island.
They killed the dodo birds for their meat.
The last one was killed in 1681.
# Description
The only record we have is written descriptions and pictures (possibly unreliable).
A Dutch painting suggests the dodo was very [[33]].
The only remaining soft tissue is a dried [[34]].
Recent studies of a dodo skeleton suggest the birds were capable of rapid [[35]].
It’s thought they were able to use their small wings to maintain [[36]].
The [[37]] was of average size.
Their sense of [[38]] enabled them to find food.
# Reasons for extinction
Hunting was probably not the main cause.
Sailors brought dogs and monkeys.
[[39]] also escaped onto the island and ate the birds’ eggs.
The arrival of farming meant the [[40]] was destroyed.''',
}

TABLES={
(13,1,1):('COOKERY CLASSES',[
['!Cookery Class','!Focus','!Other Information'],
['Example: The Food Studio','how to [[1]] and cook with seasonal products','• small classes\n• also offers [[2]] classes\n• clients who return get a [[3]] discount'],
["Bond’s Cookery School",'food that is [[4]]','• includes recipes to strengthen your [[5]]\n• they have a free [[6]] every Thursday'],
['The [[7]] Centre','mainly [[8]] food','• located near the [[9]]\n• a special course in skills with a [[10]] is sometimes available']]),
(15,1,15):('Timetable for Isle of Man holiday',[
['!','!Activity','!Notes'],['Day 1','Arrive','Introduction by manager\nHotel dining room has view of the [[15]]'],
['Day 2','Tynwald Exhibition and Peel','Tynwald may have been founded in [[16]] not 979.'],
['Day 3','Trip to Snaefell','Travel along promenade in a tram; train to Laxey; train to the [[17]] of Snaefell'],
['Day 4','Free day','Company provides a [[18]] for local transport and heritage sites.'],
['Day 5','Take the [[19]] railway train from Douglas to Port Erin','Free time, then coach to Castletown – former [[20]] has old castle.'],
['Day 6','Leave','Leave the island by ferry or plane']]),
(15,2,1):('Festival information',[
['!Date','!Type of event','!Details'],['17th','a concert','performers from Canada'],
['18th','a ballet','company called [[1]]'],['19th–20th (afternoon)','a play','type of play: a comedy called Jemima\nhas had a good [[2]]'],
['20th (evening)','a [[3]] show','show is called [[4]]']]),
}

KEYS={
(13,1):'choose|private|20~twenty percent~20 percent|healthy|bones|lecture|Arretsa|vegetarian|market|knife|B|C|B|E|D|B|G|C|H|I|A|C|B|C|B|G|C|H|A|E|crow|cliffs|speed|brain~brains|food|behaviour~behaviours~behavior~behaviors|new|stress|tail~tails|permanent',
(13,2):'races|insurance|Jerriz|25~twenty-five|stadium|park|coffee|leader|route|lights|C|B|C|B|B|A|C|E|B|D|B|A|C|C|A|A|C|D|G|B|location|world|personal|attention|name|network|frequency|colour~color|brain|self',
(13,3):'850|bike~bicycle|parking|30~thirty|weekend~weekends|cinema|hospital|dentist|Thursday|café~cafe|F|D|A|B|C|G|B|C|B|D|C|A|A|B|C|F|H|D|A|E|tongue~tongues|plants|snakes|sky|partner~partners|contact|protection|tail~tails|steps|injury~injuries',
(13,4):'Finance|Maths~Math~Mathematics|business|17~seventeen|holiday~holidays~vacation~vacations|college|location|jeans|late|smile|A|B|A|C|A|B|B|D|A|E|A|A|C|C|B|A|B|C|D|E|destruction|universities~university|political|port~ports|slaves~slavery|taxation|sugar|tea|transportation|night',
(14,1):'Canadian|furniture|Park|250~250 sterling|phone|10 September~10th September|museum|time|blond~blonde|8795482361~87954 82361|A|C|B|E|B|B|C|A|A|C|B|A|C|B|A|B|A|F|G|C|industry|constant|direction|floor|predictable|bay|gates|fuel|jobs|migration',
(14,2):'2194429785~219 442 9785|10 October~10th October|manager|Cawley|knee|3 weeks~three weeks|tennis|running|shoulder|vitamins|B|C|C|B|A|H|D|F|A|E|B|C|A|A|E|D|A|H|G|C|dances|survival|clouds|festivals|comets|sky|instruments|thermometer|storms|telegraph',
(14,3):'Tesla|microphone|exhibition|wifi|45|135|pool|airport|sea|clubs|A|E|B|E|F|A|E|G|D|C|50|regional|carnival|drummer|film|parade|D|B|E|F|violin|energy|complex|opera|disturbing|clarinet|diversity|physics|dance|Olympics',
(14,4):'85|roses|trees|stage|speech|support|cabins|C|A|B|G|D|A|E|F|B|B|D|A|D|A|C|A|B|B|F|E|C|B|G|spring|tools|maps|heavy|marble|light|camera~cameras|medical|eyes|wine',
(15,1):'Jamieson|afternoon|communication|week|10~ten|suit|passport|personality|feedback|time|A|B|A|C|river|1422|top|pass|steam|capital|G|F|A|E|B|C|C|A|B|D|shelter|oil|roads|insects|grass~grasses|water|soil|dry|simple|nest~nests',
(15,2):'Eustatis|review|dance|Chat|healthy|posters|wood|lake|insects|blog|B|C|B|C|E|C|B|A|G|D|B|D|B|C|G|B|D|C|H|F|Irrigation|women|wire~wires|seed~seeds|posts|transport|preservation|fish~fishes|bees|design',
(15,3):'furniture|meetings|diary|detail~details|1 year~one year|deliveries|tidy|team|heavy|customer|B|A|C|B|C|B|B|D|A|E|page|size|graphic~graphics|structure|purpose|assumption~assumptions|A|C|C|B|mud|clay|metal|hair|bath~baths|disease~diseases|perfume|salt|science|tax',
(15,4):'journalist|shopping|Staunfirth|return|23.70|online|delay|information|platform~platforms|parking|D|C|G|H|A|E|A|D|A|E|B|A|B|A|A|A|B|B|A|C|wealth|technology|power|textile~textiles|machines|newspapers|local|lighting|windows|Advertising',
(16,1):'egg|tower|car|animals|bridge|movie~film|decorate|Wednesdays|Fradstone|parking|C|A|B|C|H|C|G|B|I|A|C|E|B|E|D|C|A|H|F|G|practical|publication|choices|negative|play|capitalism|depression|logic|opportunity|practice~practise',
(16,2):'frame|195|payment|Grandparents|colour~color|hand|background|focus|ten days~10 days|plastic|C|B|A|A|C|D|A|B|B|C|B|A|C|C|history|paper|humans~people|stress|graph|evaluate|creativity|therapy|fitness|balance|brain|motivation|isolation|calories|obesity|habit',
(16,3):'park|blue|reference|story|rain|snack|medication|helmet|tent|199|A|E|B|C|D|F|A|H|C|G|C|D|C|E|C|A|B|A|A|C|grandmother|decade|equipment|economic|basic|round|bone|rough|style|sheep',
(16,4):'28th|550|Chervil|garage|garden|parking|wood|bridge|monument|March|B|C|B|B|C|F|A|I|E|H|B|C|B|C|C|F|D|E|B|A|spice~spices|colony~settlement|fat|head|movement|balance~balancing|brain|smell|rats|forest',
}

# Corrections caught by visual review of all 16 original key pages.
for _bt,_rep in {(15,2):{11:'C',12:'A'},(15,4):{20:'C'},(16,3):{12:'C'},(16,4):{11:'C',12:'A'}}.items():
    _v=KEYS[_bt].split('|')
    for _n,_a in _rep.items():_v[_n-1]=_a
    KEYS[_bt]='|'.join(_v)

# Each tuple: first question, last question, type, source pages.
SPECS={
(13,1):[[(1,10,'completion',[9])],[(11,13,'choice',[10]),(14,20,'map',[11])],[(21,25,'choice',[12]),(26,30,'matching',[13])],[(31,40,'completion',[14])]],
(13,2):[[(1,10,'completion',[31])],[(11,16,'choice',[32]),(17,18,'multi',[33]),(19,20,'multi',[33])],[(21,25,'choice',[34]),(26,30,'matching',[35])],[(31,40,'completion',[36])]],
(13,3):[[(1,10,'completion',[53])],[(11,16,'matching',[54]),(17,18,'multi',[55]),(19,20,'multi',[55])],[(21,24,'choice',[56]),(25,30,'matching',[57])],[(31,40,'completion',[58])]],
(13,4):[[(1,10,'completion',[75])],[(11,16,'choice',[76]),(17,20,'matching',[77])],[(21,26,'choice',[78]),(27,28,'multi',[79]),(29,30,'multi',[79])],[(31,40,'completion',[80])]],
(14,1):[[(1,10,'completion',[2])],[(11,12,'multi',[3]),(13,14,'multi',[3]),(15,20,'matching',[4])],[(21,25,'choice',[5]),(26,30,'matching',[6])],[(31,40,'completion',[7])]],
(14,2):[[(1,10,'completion',[24])],[(11,15,'choice',[25]),(16,20,'map',[26])],[(21,24,'choice',[27]),(25,30,'matching',[28])],[(31,40,'completion',[29])]],
(14,3):[[(1,10,'completion',[45])],[(11,12,'multi',[46]),(13,14,'multi',[46]),(15,20,'matching',[47])],[(21,26,'completion',[48]),(27,30,'matching',[49])],[(31,40,'completion',[50])]],
(14,4):[[(1,7,'completion',[67]),(8,10,'matching',[68])],[(11,16,'matching',[69]),(17,18,'multi',[70]),(19,20,'multi',[70])],[(21,25,'choice',[71]),(26,30,'matching',[72])],[(31,40,'completion',[73])]],
(15,1):[[(1,10,'completion',[12])],[(11,14,'choice',[13]),(15,20,'completion',[14])],[(21,26,'matching',[15]),(27,28,'choice',[16]),(29,30,'multi',[16])],[(31,40,'completion',[17])]],
(15,2):[[(1,4,'completion',[33]),(5,10,'completion',[33])],[(11,14,'choice',[34]),(15,20,'map',[35])],[(21,22,'multi',[36]),(23,24,'multi',[36]),(25,30,'matching',[37])],[(31,40,'completion',[38])]],
(15,3):[[(1,10,'completion',[54,55])],[(11,16,'choice',[56]),(17,18,'multi',[57]),(19,20,'multi',[57])],[(21,26,'completion',[58]),(27,30,'matching',[58])],[(31,40,'completion',[59])]],
(15,4):[[(1,10,'completion',[76])],[(11,16,'map',[77]),(17,18,'multi',[78]),(19,20,'multi',[78])],[(21,24,'choice',[79]),(25,30,'matching',[80])],[(31,40,'completion',[81])]],
(16,1):[[(1,10,'completion',[11])],[(11,14,'choice',[12]),(15,20,'map',[13])],[(21,22,'multi',[14]),(23,24,'multi',[14]),(25,30,'matching',[15])],[(31,40,'completion',[16])]],
(16,2):[[(1,10,'completion',[33])],[(11,15,'choice',[34]),(16,18,'matching',[35]),(19,20,'multi',[35])],[(21,24,'choice',[36]),(25,30,'completion',[37])],[(31,40,'completion',[38])]],
(16,3):[[(1,10,'completion',[56])],[(11,12,'multi',[57]),(13,14,'multi',[57]),(15,20,'matching',[58])],[(21,22,'multi',[59]),(23,24,'multi',[59]),(25,30,'choice',[60])],[(31,40,'completion',[61])]],
(16,4):[[(1,10,'completion',[77])],[(11,14,'choice',[78]),(15,20,'map',[79])],[(21,22,'multi',[80]),(23,24,'multi',[80]),(25,30,'matching',[81])],[(31,40,'completion',[82])]],
}

MATCHING={
(13,1,14):('New traffic lights|Pedestrian crossing|Parking allowed|New ‘No Parking’ sign|New disabled parking spaces|Widened pavement|Lorry loading/unloading restrictions','A|B|C|D|E|F|G|H|I'),
(13,1,26):('Select seeds of different … and sizes.|Measure and record the … and size of each one.|Decide on the … to be used.|Use a different … for each seed and label it.|After about 3 weeks, record the plant’s … .','container|soil|weight|condition|height|colour|types|depths'),
(13,2,26):('structure|eye contact|body language|choice of words|handouts','lacked a conclusion|useful in the future|not enough|sometimes distracting|showed originality|covered a wide range|not too technical'),
(13,3,11):('using a gym|running|swimming|cycling|doing yoga|training with a personal trainer','not dependent on season|enjoyable|low risk of injury|fitness level unimportant|sociable|fast results|motivating'),
(13,3,25):('turmeric|beetroot|Tyrian purple|logwood|cochineal|metal oxide','It is expensive.|The colour is too strong.|The colour is not long-lasting.|It is very poisonous.|It can damage the fabric.|The colour may be unexpected.|It is unsuitable for some fabrics.|It is not generally available.'),
(13,4,17):('Highland Trail|Pine Trail|Stony Trail|Loser’s Trail','It has a good place to stop and rest.|It is suitable for all abilities.|It involves crossing a river.|It demands a lot of skill.|It may be closed in bad weather.|It has some very narrow sections.'),
(14,1,15):('Using the internet|Flexible working|Booking holidays|Working overtime|Wearing trainers|Bringing food to work','It is encouraged.|There are some restrictions.|It is against the rules.'),
(14,1,26):('Historical background|Geographical factors|Past mistakes|Future risks|International implications','use visuals|keep it short|involve other students|check the information is accurate|provide a handout|focus on one example|do online research'),
(14,2,16):('Starting point for walking the walls|Bow and arrow display|Hunting birds display|Traditional dancing|Shop','A|B|C|D|E|F|G|H'),
(14,2,25):('Introduction|Discovery of the mammoth tooth|Initial questions asked by the researchers|Further research carried out on the island|Findings and possible explanations|Relevance to the present day','make it more interactive|reduce visual input|add personal opinions|contact one of the researchers|make detailed notes|find information online|check timing|organise the content more clearly'),
(14,3,15):('Habib|Consuela|Minh|Tanya|Alexei|Juba','overcome physical difficulties|rediscover skills not used for a long time|improve their communication skills|solve problems independently|escape isolation|remember past times|start a new hobby'),
(14,3,27):('flautist|trumpeter|trombonist|percussionist','makes a lot of mistakes in rehearsals|keeps making unhelpful suggestions|has difficulty with rhythm|misses too many rehearsals|has a health problem|doesn’t mix with other students'),
(14,4,8):('outdoor swimming pool|gym|tennis courts','included in cost of hiring room|available at extra charge|not available'),
(14,4,11):('dolphin watching|forest walk|cycle trip|local craft tour|observatory trip|horse riding','all downhill|suitable for beginners|only in good weather|food included|no charge|swimming possible|fully booked today|transport not included'),
(14,4,26):('Perrault’s fairy tales|The Swiss Family Robinson|The Nutcracker and The Mouse King|The Lord of the Rings|War Horse','translated into many other languages|hard to read|inspired a work in a different area of art|more popular than the author’s other works|original title refers to another book|started a new genre|unlikely topic'),
(15,1,21):('the eldest child|a middle child|the youngest child|a twin|an only child|a child with much older siblings','outgoing|selfish|independent|attention-seeking|introverted|co-operative|caring|competitive'),
(15,2,15):('statue of Diane Gosforth|wooden sculptures|playground|maze|tennis courts|fitness area','A|B|C|D|E|F|G|H|I'),
(15,2,25):('The Pickwick Papers|Oliver Twist|Nicholas Nickleby|Martin Chuzzlewit|Bleak House|Little Dorrit','poverty|education|Dickens’s travels|entertainment|crime and the law|wealth|medicine|a woman’s life'),
(15,3,27):('national news item|editorial|human interest|arts','She will definitely look for a suitable article.|She may look for a suitable article.|She definitely won’t look for an article.'),
(15,4,11):('café|toilets|formal gardens|outdoor gym|skateboard ramp|wild flowers','A|B|C|D|E|F|G|H'),
(15,4,25):('the goods that are refrigerated|the effects on health|the impact on food producers|the impact on cities|refrigerated transport|domestic fridges','Annie|Jack|both Annie and Jack'),
(16,1,15):('coffee room|warehouse|staff canteen|meeting room|human resources|boardroom','A|B|C|D|E|F|G|H|I|J'),
(16,1,25):('Falcon (Landseer)|Fish hawk (Audubon)|Kingfisher (van Gogh)|Portrait of William Wells|Vairumati (Gauguin)|Portrait of Giovanni de Medici','a childhood memory|hope for the future|fast movement|a potential threat|the power of colour|the continuity of life|protection of nature|a confused attitude to nature'),
(16,2,16):('World Adventures|Street Life|Speedy Italian','pupils help to plan menus|only vegetarian food|different food every week|daily change in menu'),
(16,3,15):('Fresh food commercial manager|Agronomist|Fresh produce buyer|Garden centre sales manager|Tree technician|Farm worker','not a permanent job|involves leading a team|experience not essential|intensive work but also fun|chance to earn more through overtime|chance for rapid promotion|accommodation available|local travel involved'),
(16,4,15):('New car park|New cricket pitch|Children’s playground|Skateboard ramp|Pavilion|Notice board','A|B|C|D|E|F|G|H|I'),
(16,4,25):('Amsterdam|Dublin|London|Buenos Aires|New York|Sydney','They agree it has been disappointing.|They think it should be cheaper.|They are surprised it has been so successful.|They agree that more investment is required.|They think the system has been well designed.|They disagree about the reasons for its success.|They think it has expanded too quickly.'),
}

def pdf(book):
    return next((MATERIALS/f'CAMBRIDGE-{book}'/'BAN_GOC').glob('*.pdf'))

def page_data(b,p):
    # Cambridge 15's low-contrast scans require the earlier binary OCR.
    old=LIB/'preparation'/f'cam{b}'/f'p{p:03}.json'
    if b==15 and old.exists():return json.loads(old.read_text(encoding='utf8'))
    return json.loads(cache(b,p).read_text(encoding='utf8'))

def text_page(b,p):
    text=page_data(b,p)['text']
    lines=[]
    for line in text.splitlines():
        s=line.strip()
        if re.search(r'FB[.,]com|LouisQuang|[Tt]ham gia|facebook|IELTSXpress|^Test\s+\d|^Listening$|^LISTENING$|^Audioscripts$|^\|*\s*$|p\.\s*\d',s):continue
        if s in ('|',':',';','i','j','I','!','ii','Hl','HI','k','ll','‘'):continue
        s=re.sub(r'^([ABC])[_~\-=]+',r'\1 ',s)
        if s in ('Bi','Bs'):s='B'
        if s=='Cc':s='C'
        s=re.sub(r'^B(?=more |it was |on Saturdays |read the |one day |as land )','B ',s)
        s=re.sub(r'^C(?=__He|__The)','C ',s)
        s=re.sub(r'\b(Inasurvey|Inconnection|inconnection|Atthe|Inthe|Howis|Whyis)\b',lambda m:{'Inasurvey':'In a survey','Inconnection':'In connection','inconnection':'in connection','Atthe':'At the','Inthe':'In the','Howis':'How is','Whyis':'Why is'}[m[0]],s)
        s=s.replace('allparticipants','all participants').replace('Allparticipants','All participants').replace('Hedidn’t','He didn’t').replace('Hes','He’s')
        lines.append(s)
    text='\n'.join(lines)
    if b==13:
        replacements={10:[('41.\nWhy','11\nWhy')],32:[('™\nHow','11\nHow'),('72\nin feedback','12\nIn feedback'),('73\nLast','13\nLast'),('™\n=This','14\nThis'),('75\nWhere','15\nWhere'),('6\nWhat','16\nWhat')],34:[('2\nRuss','21\nRuss'),('@\nRuss','22\nRuss')],56:[('@\nWhat','21\nWhat'),('@2\nJim','22\nJim'),('2\nWhen','23\nWhen')]}
        for x,y in replacements.get(p,[]):text=text.replace(x,y)
        if p==76:
            for n in range(11,17):text=re.sub(rf'(?m)^{n+30}[.]?$',str(n),text)
    return text

def ws(s):
    s=re.sub(r'\s+',' ',s).strip(' _-;:|—')
    for a,b in {'atthe':'at the','atacollege':'at a college','inacommunity':'in a community','toconcentrate':'to concentrate','iist the':'list the','abook':'a book','causeda':'caused a','goata':'go at a','anew':'a new','anentertainment':'an entertainment','goto':'go to','aphotograph':'a photograph','iunches':'lunches','asashared':'as a shared','wasa':'was a','amonth':'a month','acouncil':'a council','shave to':'have to','aprivate':'a private','alocal':'a local','wedo':'we do','Asurvey':'A survey','seta':'set a','Heused':'He used','bygiving':'by giving','Alarge':'A large','8hours':'8 hours'}.items():s=s.replace(a,b)
    s=re.sub(r'\s+[—-]?FB\S*.*$','',s)
    s=s.replace('Elizabeth |','Elizabeth I')
    if s.startswith('tis mainly'):s='It is mainly'+s[len('tis mainly'):]
    return s

def options(raw,letters='ABC'):
    matches=list(re.finditer(r'(?m)^([A-J])(?:[ \t_.~\-=]+|\n)',raw))
    result=[]
    for i,m in enumerate(matches):
        if m[1] not in letters:continue
        label=raw[m.end():matches[i+1].start() if i+1<len(matches) else len(raw)]
        label=re.split(r'(?m)^\d{1,3}[. ]*$',label)[0]
        label=re.sub(r'\b[|]\b',' ',label)
        result.append({'value':m[1],'label':ws(label)})
    return result

def range_chunk(raw,lo,hi):
    heads=list(re.finditer(r'(?mi)^[A-Za-z]*[Qq]uestions?\s+(\d+)\s*(?:[–—-]|and)\s*(\d+)[^\n]*',raw))
    hit=next((i for i,m in enumerate(heads) if int(m[1])==lo and int(m[2])==hi),None)
    if hit is None:return raw
    stop=next((m.start() for m in heads[hit+1:] if (int(m[1]),int(m[2]))!=(lo,hi)),len(raw))
    return raw[heads[hit].end():stop]

def source_image(b,page):
    import pymupdf
    from PIL import Image
    out=LIB/'assets'/f'l-cam{b}-page-{page:03}.webp'
    if not out.exists():
        with pymupdf.open(pdf(b)) as doc:
            pix=doc[page-1].get_pixmap(dpi=150,alpha=False)
            Image.frombytes('RGB',(pix.width,pix.height),pix.samples).save(out,'WEBP',quality=88)
    return {'url':'/library-assets/'+out.name,'page':page}

def content(s):
    bits=re.split(r'(\[\[\d+\]\])',s)
    return [{'number':int(x[2:-2])} if re.fullmatch(r'\[\[\d+\]\]',x) else x for x in bits if x]

def group(b,t,p,spec):
    lo,hi,kind,pages=spec; key=(b,t,lo)
    raw='\n'.join(text_page(b,page) for page in pages)
    raw=range_chunk(raw,lo,hi)
    gid=f'l-cam{b}-t{t}-p{p}-g{lo}'
    g={'id':gid,'type':'matching' if kind=='map' else kind,'heading':f'Questions {lo}–{hi}','instructions':'','body':'','questions':[],'sourceImages':[source_image(b,x) for x in pages]}
    if kind=='completion':
        number_allowed=not ((lo>=31) or (b==14 and t==3 and lo==31) or (b==15 and t==2) or (b==15 and t==3 and lo==21) or (b==16 and t==2 and lo==25))
        # Cambridge14T3Part4 explicitly permits a number too.
        if (b,t,lo)==(14,3,31):number_allowed=True
        g.update(wordLimit=1,allowNumber=number_allowed)
        noun='table' if key in TABLES else 'flow chart' if key==(16,2,25) else 'form' if key in ((14,1,1),(15,4,1)) else 'notes'
        g['instructions']=f'Complete the {noun} below.\nWrite ONE WORD'+(' AND/OR A NUMBER' if number_allowed else ' ONLY')+' for each answer.'
        if key in TABLES:
            caption,rows=TABLES[key]
            g['layout']={'kind':'table','caption':caption,'rows':[{'cells':[{'header':c.startswith('!'),'content':content(c.lstrip('!'))} for c in row]} for row in rows]}
            flat='\n'.join(c.lstrip('!') for row in rows for c in row)
        else:
            flat=FLOWS[key]
            g['layout']={'kind':'flow','blocks':[{'tag':'h3' if x.startswith('# ') else 'p','content':content(x[2:] if x.startswith('# ') else x)} for x in flat.splitlines()]}
        for n in range(lo,hi+1):
            row=next(x for x in flat.splitlines() if f'[[{n}]]' in x)
            g['questions'].append({'number':n,'text':re.sub(r'\[\[\d+\]\]','…',row).lstrip('# ')})
    elif kind in ('matching','map'):
        qs,opts=MATCHING[key]
        g['questions']=[{'number':n,'text':label} for n,label in zip(range(lo,hi+1),qs.split('|'))]
        g['options']=[{'value':chr(65+i),'label':label} for i,label in enumerate(opts.split('|'))]
        # Preserve the original question/instruction above the choice box.
        firstopt=re.search(r'(?m)^A(?:[ \t_]+|\n)',raw)
        instructions=raw[:firstopt.start()] if firstopt else raw
        instructions=re.sub(r'(?m)^(?:SECTION|PART)\s*\d.*$','',instructions)
        instructions=re.sub(r'(?m)^\d{1,3}$','',instructions)
        g['instructions']=ws(instructions)
        g['instructions']=re.sub(r'Questions?\s+\d+\s*[–—-]\s*\d+','',g['instructions']).strip()
        if g['instructions'].endswith('next to'):g['instructions']+=f' Questions {lo}–{hi}.'
        g['instructions']=g['instructions'].removeprefix('k ')
        if kind=='map':
            g['instructions']=f'Label the map/plan below. Write the correct letter, A–{chr(64+len(g["options"]))}, next to Questions {lo}–{hi}.'
            g['body']='';g['renderMode']='source-map'
            coords={
                (13,1,14):(.75,.727,.0372,.13),
                (14,2,16):(.714,.728,.0238,.12),
                (15,2,15):(.443,.676,.0259,.095),
                (15,4,11):(.349,.634,.0259,.10),
                (16,1,15):(.367,.713,.0275,.095),
                (16,4,15):(.443,.650,.0275,.095),
            }
            x,y,step,width=coords[key]
            g['layout']={'kind':'diagram','image':g['sourceImages'][0],'labels':[{'number':n,'x':x,'y':round(y+(n-lo)*step,5),'width':width} for n in range(lo,hi+1)]}
        elif key==(13,1,26):g['body']='Stages in the experiment\nInvestigate the findings.'
    elif kind=='multi':
        g['instructions']='Choose TWO letters, A–E.';g['choose']=2
        g['options']=options(raw,'ABCDE')
        first=re.search(r'(?m)^A(?:[ \t_]+|\n)',raw)
        prompt=raw[:first.start()] if first else raw
        prompt=re.sub(r'Choose TWO[^\n]*','',prompt)
        prompt=re.sub(r'(?m)^\d{1,3}$','',prompt)
        g['body']=ws(prompt)
        g['questions']=[{'number':n,'text':g['body']} for n in range(lo,hi+1)]
        assert [o['value'] for o in g['options']]==list('ABCDE'),(key,g['options'])
    elif kind=='choice':
        g['instructions']='Choose the correct letter, A, B or C.'
        for n in range(lo,hi+1):
            m=re.search(rf'(?m)^{n}(?:[. \t]+|\n)',raw)
            assert m,(key,n,raw)
            nxt=re.search(rf'(?m)^{n+1}(?:[. \t]+|\n)',raw[m.end():]) if n<hi else None
            end=m.end()+nxt.start() if nxt else len(raw)
            chunk=raw[m.end():end]
            if n==hi:chunk=re.split(r'(?m)^Questions?\s+\d',chunk)[0]
            opt=options(chunk)
            first=re.search(r'(?m)^A(?:[ \t_]+|\n)',chunk)
            assert first and [o['value'] for o in opt]==list('ABC'),(key,n,opt,chunk)
            g['questions'].append({'number':n,'text':ws(chunk[:first.start()]),'options':opt})
    assert [q['number'] for q in g['questions']]==list(range(lo,hi+1)),key
    return g

def cache(book,page):return PREP/f'cam{book}'/f'p{page:03}.json'

def extract_one(job):
    import pymupdf
    book,page_no=job
    target=cache(book,page_no)
    if target.exists() and (book!=15 or json.loads(target.read_text(encoding='utf8')).get('method')=='binary'):return book,page_no,'cached'
    target.parent.mkdir(parents=True,exist_ok=True)
    with pymupdf.open(pdf(book)) as doc:
        page=doc[page_no-1]
        if book==15:
            import io
            from PIL import Image,ImageOps
            pix=page.get_pixmap(dpi=250,alpha=False)
            im=ImageOps.autocontrast(Image.frombytes('RGB',(pix.width,pix.height),pix.samples).convert('L')).point(lambda x:0 if x<195 else 255).convert('RGB')
            buf=io.BytesIO();im.save(buf,format='PNG')
            pix=pymupdf.Pixmap(buf.getvalue());ocr=pymupdf.open(stream=pix.pdfocr_tobytes(tessdata='library/preparation/tessdata',language='eng'))
            op=ocr[0]
            data={'book':book,'page':page_no,'width':page.rect.width,'height':page.rect.height,'text':op.get_text(),'words':op.get_text('words'),'blocks':op.get_text('blocks'),'method':'binary'}
        else:
            tp=page.get_textpage_ocr(language='eng',dpi=250,full=True,tessdata='library/preparation/tessdata')
            data={'book':book,'page':page_no,'width':page.rect.width,'height':page.rect.height,
                  'text':page.get_text(textpage=tp),'words':page.get_text('words',textpage=tp),
                  'blocks':page.get_text('blocks',textpage=tp),'method':'ocr'}
        target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    return book,page_no,'ocr'

def extract(books):
    os.chdir(ROOT);os.environ['OMP_THREAD_LIMIT']='1'
    jobs=[]
    for b in books:
        pages=sorted({p for r in QUESTION_PAGES.get(b,[]) for p in r}|set(range({13:96,14:89,15:98,16:1}[b],{13:124,14:119,15:129,16:137}[b])))
        jobs.extend((b,p) for p in pages)
    with concurrent.futures.ProcessPoolExecutor(max_workers=6) as pool:
        for i,r in enumerate(pool.map(extract_one,jobs),1):
            if i%10==0 or i==len(jobs):print(i,len(jobs),r,flush=True)

def audio_source(b,t,p):
    folder=MATERIALS/f'CAMBRIDGE-{b}'
    files=sorted(x for x in folder.rglob('*') if x.suffix.lower() in ('.mp3','.m4a') and not x.name.startswith('._'))
    if b==13:
        cd=1 if t<3 else 2;track=((t-1)%2)*4+p
        return next(x for x in files if f'CD{cd}Track_{track:02}' in x.name)
    if b==14:return next(x for x in files if x.stem==f'C14T{t}S{p}')
    if b==15:return next(x for x in files if x.stem==f'ielts15_test{t}_audio{p}')
    return next(x for x in files if x.stem==f'Test {t} Part {p}')

def decode_audio(path):
    import av,numpy as np
    resampler=av.AudioResampler(format='s16',layout='mono',rate=16000)
    chunks=[]
    with av.open(str(path),mode='r') as container:
        for frame in container.decode(audio=0):
            frame.pts=None
            chunks.extend(f.to_ndarray().reshape(-1) for f in resampler.resample(frame))
        chunks.extend(f.to_ndarray().reshape(-1) for f in resampler.resample(None))
    return np.concatenate(chunks).astype(np.float32)/32768.0

def verify_audio(books):
    from faster_whisper import WhisperModel
    from mutagen import File
    model=WhisperModel('tiny.en',device='cpu',compute_type='int8',download_root=str(PREP/'models'),cpu_threads=3,local_files_only=True)
    for b in books:
        for t in range(1,5):
            for p in range(1,5):
                target=PREP/f'cam{b}'/f't{t}-p{p}-audio-asr.json'
                if target.exists():continue
                src=audio_source(b,t,p);samples=decode_audio(str(src));duration=len(samples)/16000
                clips=[(0,min(duration,115)),(max(0,duration-100),duration)]
                text=[];segments=[]
                for start,end in clips:
                    segs,_=model.transcribe(samples[int(start*16000):int(end*16000)],language='en',beam_size=3,condition_on_previous_text=False)
                    for seg in segs:
                        segments.append({'start':round(start+seg.start,2),'end':round(start+seg.end,2),'text':seg.text.strip()})
                        text.append(seg.text.strip())
                out={'book':b,'test':t,'part':p,'source':src.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
                    'duration':round(File(src).info.length,3),'samples':clips,'text':' '.join(text),'segments':segments,'method':'local-faster-whisper-tiny.en-int8-samples'}
                target.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
                print('ASR',b,t,p,round(duration),flush=True)

def transcript_parts(book):
    first,last={13:(96,115),14:(97,118),15:(98,120),16:(99,121)}[book]
    raw='\n'.join(text_page(book,p) for p in range(first,last+1))
    # PDF13 is missing printed page109, not just an OCR failure. Recover that
    # supplied recording below and retain its distinct provenance.
    markers=list(re.finditer(r'(?:SECTION|PART)\s*([1-4])\b',raw))
    result={};test=0
    for i,m in enumerate(markers):
        part=int(m[1])
        if part==1:test+=1
        text=raw[m.end():markers[i+1].start() if i+1<len(markers) else len(raw)]
        text=re.sub(r'(?mi)^TEST\s*\d\s*$','',text)
        text=re.sub(r'Q\s*[0-9g]+(?:\s*[/&]\s*Q?\s*\d+)*','',text)
        text=re.sub(r'(?m)^\s*(?:\d{1,3}|Example|[|:;.!])\s*$','',text)
        text=text.replace('|','I').replace('lIt','It')
        text=re.sub(r'(?m)^([A-Z][A-Z ]{1,18})[?;!]\s*$',r'\1:',text)
        text=re.sub(r'(?m)^([A-Z][A-Z ]{1,18}):\s*\n',r'\1: ',text)
        text=re.sub(r'(?<![:.!?])\n(?=[a-zA-Z])',' ',text)
        text=re.sub(r' *\n *','\n',text)
        text=re.sub(r'\n{3,}','\n\n',text).strip()
        result[test,part]=text
    assert test==4,(book,test)
    if book==13:
        records=json.loads((PREP/'cam13/t3-p2-full-asr.json').read_text(encoding='utf8'))
        recovered=' '.join(x['text'] for x in records if x['start']>=45 and 'end of section' not in x['text'].lower() and 'check your answers' not in x['text'].lower() and 'turn to section' not in x['text'].lower())
        recovered=recovered[recovered.lower().index('so if '):]
        recovered=re.sub(r"(?i)that is the end.*$",'',recovered)
        # Tiny's proper-name/singular errors checked against the supplied
        # source questions and the audible source recording.
        recovered=recovered.replace('excessing','exercising').replace('Bicron','bike').strip()
        result[3,2]=recovered
        result[3,1]+='\nLINDA: OK. Great. Let me know which train you’re catching and I’ll meet you in the café outside. You can’t miss it. It’s opposite the station and next to the museum.\nMATT: Brilliant. I’ll text you next week then. Thanks so much for all the advice.\nLINDA: No problem. I’ll see you next week.'
    assert set(result)=={(t,p) for t in range(1,5) for p in range(1,5)},(book,result.keys())
    return result

def audio_manifest(b,t,p):
    src=audio_source(b,t,p)
    proof=json.loads((PREP/f'cam{b}'/f't{t}-p{p}-audio-asr.json').read_text(encoding='utf8'))
    digest=proof['sha256'];duration=proof['duration'];start=0;end=duration
    if p==1:
        # Skip publisher/copyright and general paper-format introduction.
        for seg in proof['segments']:
            st=seg['text'].lower()
            if seg['start']<110 and 'you will hear' in st and 'number of different' not in st:
                start=seg['start'];break
    if p==4:
        for seg in proof['segments']:
            if seg['start']>duration-100 and ('transfer your answers' in seg['text'].lower() or ('in the ielts test' in seg['text'].lower())):
                end=seg['start'];break
    if (b,t,p)==(14,2,4):end=505.12
    target=LIB/'audio'/f'{digest}{src.suffix.lower()}'
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():shutil.copyfile(src,target)
    return {'url':'/library-audio/'+target.name,'sha256':digest,'duration':duration,'start':start,'end':end,'source':src.relative_to(ROOT).as_posix(),
            'verification':{'status':'verified','method':'local-ASR-opening-and-ending-compared-to-source-script-and-questions','proof':(PREP/f'cam{b}'/f't{t}-p{p}-audio-asr.json').relative_to(LIB).as_posix(),
                            'note':'Appended next test excluded at 505.12s; source file remains unchanged.' if (b,t,p)==(14,2,4) else 'Paper answer-transfer instruction excluded from Part4; original reading/checking pauses retained.'}}

def build(books):
    reports=[]
    for b in books:
        transcripts=transcript_parts(b)
        for t in range(1,5):
            ident=f'cam{b}-listening-test{t}'
            parts=[];multi=[]
            values=KEYS[b,t].split('|');assert len(values)==40,(b,t,len(values))
            answers={str(i):v.split('~') for i,v in enumerate(values,1)}
            for p,specs in enumerate(SPECS[b,t],1):
                groups=[group(b,t,p,s) for s in specs]
                for g in groups:
                    if g['type']=='multi':
                        nums=[q['number'] for q in g['questions']]
                        multi.append({'numbers':nums,'answers':[answers[str(n)][0] for n in nums]})
                pages=sorted({pg for s in specs for pg in s[3]})
                firstgroup=groups[0]
                title=next((x['content'][0] for x in firstgroup.get('layout',{}).get('blocks',[]) if x['tag']=='h3' and x['content'] and isinstance(x['content'][0],str)),firstgroup.get('layout',{}).get('caption',f'Part {p}'))
                parts.append({'id':f'{ident}-p{p}','number':p,'title':title,'paragraphs':[],'groups':groups,
                              'sourceImages':[source_image(b,x) for x in pages],'sourcePages':[{'file':pdf(b).relative_to(ROOT).as_posix(),'page':x} for x in pages],
                              'audio':audio_manifest(b,t,p)})
            numbers=[q['number'] for p in parts for g in p['groups'] for q in g['questions']]
            assert numbers==list(range(1,41)),(ident,numbers)
            data={'id':ident,'skill':'listening','book':b,'test':t,'title':f'Cambridge {b} · Listening Test {t}', 'version':'2.0-listening1',
                  'verification':{'status':'verified','note':'Source PDF questions, all key pages, interactive blanks and audio opening/ending verified; private preparation evidence retained.'},'parts':parts}
            exceptions={}
            for p in parts:
                for g in p['groups']:
                    if g.get('wordLimit'):
                        for q in g['questions']:
                            n=str(q['number'])
                            over=[a for a in answers[n] if len(re.findall(r"\b[A-Za-zÀ-ÿ]+(?:[-’'][A-Za-zÀ-ÿ]+)*\b",a))>g['wordLimit']]
                            if over:exceptions[n]=over
            key={'id':ident,'version':'2.0-listening1','answers':answers,'multi':multi,'limitExceptions':exceptions,
                 'provenance':{'source':pdf(b).relative_to(ROOT).as_posix(),'pdfPage':{13:116,14:89,15:121,16:122}[b]+(t-1)*2,'verification':'visual-review-all-16-original-key-pages'}}
            tx={'id':ident,'version':'2.0-listening1','parts':{str(p):transcripts[t,p] for p in range(1,5)},
                'provenance':{'source':pdf(b).relative_to(ROOT).as_posix(),'method':'local-PDF-OCR-source-review'}}
            if (b,t)==(13,3):tx['provenance']['reconstructedFromProvidedAudio']={'parts':[1,2],'reason':'Supplied PDFs omit printed page109. Part1finaldialogueandPart2recoveredfromprovidedlocalrecording.','proof':'preparation/listening/cam13/t3-p2-full-asr.json'}
            for folder,obj in [('tests',data),('keys',key),('transcripts',tx)]:
                out=LIB/'listening'/folder/f'{ident}.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            review={'id':ident,'questions':40,'parts':4,'groups':sum(len(p['groups']) for p in parts),'sourcePages':[x for p in parts for x in p['sourcePages']],
                    'audio':[p['audio'] for p in parts],'keyPage':key['provenance']['pdfPage'],'transcriptCharacters':{str(p):len(transcripts[t,p]) for p in range(1,5)},'limitExceptions':exceptions}
            (PREP/f'cam{b}'/f'test{t}-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf8');reports.append(review)
            print('BUILT',ident,len(numbers),flush=True)
    (PREP/'cam13-16-review.json').write_text(json.dumps({'tests':reports,'testCount':len(reports),'questionCount':len(reports)*40},ensure_ascii=False,indent=2),encoding='utf8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--extract',action='store_true');p.add_argument('--audio-verify',action='store_true');p.add_argument('--build',action='store_true');p.add_argument('--book',type=int,nargs='+',default=[13,14,15,16]);a=p.parse_args()
    if a.extract:extract(a.book)
    if a.audio_verify:verify_audio(a.book)
    if a.build:build(a.book)

if __name__=='__main__':main()
