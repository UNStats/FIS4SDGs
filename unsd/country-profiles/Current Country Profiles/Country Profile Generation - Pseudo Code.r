timePeriod >= 2000
HIV.filter!= "SH_HIV_INCDALLAGEBOTHSEX"
GeoAreaName=="Sint Maarten (Dutch part)\t" <- "Sint Maarten (Dutch part)"
Set number of zeroes


# Release = 2018.Q4.G.02

# Read conditions used for each series in country profiles

   C.Profile.Conditions_20181119.xlsx
   filter(Profile.Series,Profile.Series==1)
   filter(Profile.Series,P.IndicatorCode != "C200203") #removing the duplicate datapoints of this multipurpose series

   RefAreaDisaggregated_BYAREA <<- read.xlsx("Y:/SSB/SDGs/SDG Database/2. Country Data/2017/4. Data Validation/1. Documents and Reference Files/REF_AREA_DISAGGREGATED_Country_Region_World_2018.xlsx", sheetName="REF_AREA_DISAGGREGATED") #create the reference area table

 
# For each country and series used in country profiles, pull the data with dimension values fixed and :
   
  - countyr
    - goal
    - target
        - indicator
          - series
            - dimensions (fixed)
              - attributes
              - years
              - values

# Example: 
  url <- "https://unstats.un.org/SDGAPI/v1/sdg/Series/SI_POV_EMP1/GeoArea/818/DataSlice?dimensions=%5B%7Bname%3A%22Age%22%2Cvalues%3A%5B%2215%2B%22%5D%7D%2C%20%7Bname%3A%22Sex%22%2Cvalues%3A%5B%22BOTHSEX%22%5D%7D%5D&timePeriods=%5B%222000%22%2C%20%222005%22%5D"

#Information about status of progress: decline/increase?\
  if (min.obs > max.obs)
    prog <- DA3.Down 
    # Example: "declined from", "down from"
  else if (min.obs < max.obs)
    prog <- DA3.Up
    # Example: "increased from", "up from"
  else na

#prog.15
  if min.obs < 0.01 then "nearly no coverage" else [min.obs + unit]

#prog.10
  if max.obs < 10 down else up

#prog.12
  if max.obs > 0 then up else down

#prog mmr.min
  if min.obs > 1 then "deaths" else "death"

#prog mmr.max
  if max.obs > 1 then "deaths" else "death"

#Function for "rounding in commerce" - "kaufmaenische Rundung"
round2 = function(x, n) {
  posneg = sign(x)
  z = abs(x)*10^n
  z = z + 0.5
  z = trunc(z)
  z = z/10^n
  z*posneg
}

replace ">" with "greater than " 
replace "<" with "less than "

if obs < 0.99 then round to 2 decimals
if obs >= 0.99 and obs <= 10 then round to 1 decimal
if obs > 10 then round to 0 decimals

n.yr      # number of years available
min.yr    # first year available
max.yr    # most recent year available
  
min.obs   # data value in the first year available
max.obs   # data value in the most recent year available

median.obs # median data value

dif.obs <- abs(max.obs - min.obs)  # if both min.obs and max.obs are numeric:

#-----------------------------------
# Text type 1
#-----------------------------------

  @@@@ MULTIPLE VALUES, STARTING EARLIER THAN 2010, WITH RELATIVELY LARGE RANGE BETWEEN FIRST AND LAST, AND AWAY FROM MEDIAN @@@@
  # if ( dif.obs >= 0.05 * abs(max.obs) & max.obs is not censored & max.obs >= .25*median.obs & min.yr < 2010 & n.yr > 1)
    text <- paste(DA3.1 ,prog, min.obs, unit," in ", min.yr," to ", max.obs, unit, " in ",max.yr,"."
    # example: "The proportion of the population living below the extreme poverty line [prog] [min.obs+unit] in [min.yr] to [max.obs+unit] in [max.year]"
  # else
    text <- paste(DA2.1, max.obs, unit," in ", max.yr, "."
    # example: "The proportion of the population living below the extreme poverty line was approximately [max.obs+unit] in [max.year]"
  
#-----------------------------------
# Text type 2
#-----------------------------------

    text <- paste("In ", max.yr,", ", max.obs, unit, DA2.1,".")
    # example: "In [max.yr], [max.obs+unit] of the country's workers and their families were living on less than 1.90 US dollars per person per day." 

#-----------------------------------
# Text type 3
#-----------------------------------

    text <- paste("In", max.yr,", ", DA2.1, max.obs,unit, DA2.2,"."
    # example: "In [max.yr],  there were about [max.obs+unit] of children under age 5 whose births were registered with a civil authority." 

#-----------------------------------
# Text type 4
#-----------------------------------

    text <- paste(DA2.1, max.obs," in ", max.yr, ", meaning ", max.obs*100, DA2.2,".")
    # example: "Gender parity index for achievement in mathematics at the end of primary education was [max.obs] in [max.yr], meaning [max.obs * 100] girls per 100 boys achieved at least a minimum proficiency level in mathematics" 

#-----------------------------------
# Text type 7
#-----------------------------------

    text <- paste(DA2.1, max.obs, unit, " in ", max.yr, ".")
    # example: "The proportion of the population suffering from hunger was [max.obs + unit] in [max.yr]." 
  
#-----------------------------------
# Text type 8
#-----------------------------------
  
    text <- paste("In", max.yr, ", ", max.obs, unit, DA2.1, ".")
    # example: "In [max.yr], [max.obs + unit] of the population relied primarily on clean fuels and technology"

#-----------------------------------
# Text type 9
#-----------------------------------


  @@@@ MULTIPLE VALUES, STARTING EARLIER THAN 2010, WITH RELATIVELY LARGE RANGE BETWEEN FIRST AND LAST, AND AWAY FROM MEDIAN @@@@
  # if ( dif.obs >= 0.05 * abs(max.obs) & max.obs is not censored & max.obs >= .25*median.obs & min.yr < 2010 & n.yr > 1)
    text <- paste("In", max.yr, ", ", DA2.1, max.obs, unit,", ", prog, min.obs, secondUnit," in ",min.yr, "."
    # example: "In [max.yr], investment in research and development (R&D) stood at [max.obs + unit], [prog] [min.obs+unit] in [min.yr]"
  # else
    text <- paste("In", max.yr, ", ", DA2.1, max.obs, unit,"."
    # example: "In [max.yr], investment in research and development (R&D) stood at [max.obs + unit]"  

#-----------------------------------
# Text type 10
#-----------------------------------

  text <- paste("In", max.yr, ", ", DA2.1, max.obs, unit,".",prog.10,".")
  # example: "In [max.yr], the annual population-weighted average mean concentration of fine suspended particles of less than 2.5 microns in diameters (PM2.5) was about [max.obs+unit].  This is below the maximum level for safety set by WHO of 10 micrograms per cubic metre.

#-----------------------------------
# Text type 11
#-----------------------------------
 
  text <- paste("In", max.yr, ", ", DA2.1, max.obs, unit,".")
  # example: "In [max.yr], the intentional homicide rate was [max.obs+unit]."

#-----------------------------------
# Text type 12
#-----------------------------------

  text <- paste("As of ", max.yr, ", ", GeoAreaName, prog.12, ".",sep = "")
  # example: "As of [max.yr], [GeoAreaName] [prog.12]

#-----------------------------------
# Text type 13
#-----------------------------------
  text <- paste("In", max.yr, ", ", DA2.1, max.obs*100, unit, DA2.2,".")
  # example: "In [max.yr], there were about [max.obs*100 + unit] in every 100,000 uninfected population that became newly infected with HIV."

#-----------------------------------
# Text type 14
#-----------------------------------

  @@@@ MULTIPLE VALUES, STARTING EARLIER THAN 2010, WITH RELATIVELY LARGE RANGE BETWEEN FIRST AND LAST, AND AWAY FROM MEDIAN @@@@
  # if ( dif.obs >= 0.05 * abs(max.obs) & max.obs is not censored & max.obs >= .25*median.obs & min.yr < 2010 & n.yr > 1)
    {text <- paste(DA3.1, prog, min.obs, prog.mmr.min, unit," in ",min.yr," to ",max.obs,prog.mmr.max,unit," in ",max.yr,".")
    # example: "The maternal mortality ratio [prog] [min.obs + prog.mmr.min + unit] in [min.yr] to [max.obs + prog.mmr.max + unit] in [max.yr]"
  # else
    text <- paste(DA2.1, max.obs, prog.mmr.max, unit," in ", min.yr, ".")
    # example: "The maternal mortality ratio was [max.obs + prog.mmr.max + unit] in [max.yr]"
  

#-----------------------------------
# Text type 15
#-----------------------------------

  @@@@ MULTIPLE VALUES, STARTING EARLIER THAN 2010, WITH RELATIVELY LARGE RANGE BETWEEN FIRST AND LAST, AND AWAY FROM MEDIAN @@@@
  # if ( dif.obs >= 0.05 * abs(max.obs) & max.obs is not censored & max.obs >= .25*median.obs & min.yr < 2010 & n.yr > 1)
    text <- paste("In", max.yr,", ", DA2.1, max.obs, unit,",",prog, prog.15," in ",min.yr,".")
    # example: "In [max.yr], fixed-broadband internet penetration reached [max.obs + unit], [prog] [prog.15] in [min.yr]."
  # else
    text <- paste("In", max.yr,", ", DA2.1, max.obs, unit,".")
    # example: "In [max.yr], fixed-broadband internet penetration reached [max.obs + unit]"
  