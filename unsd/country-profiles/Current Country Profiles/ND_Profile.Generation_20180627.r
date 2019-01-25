#Background Document:Y:\SSB\SDGs\SDG Database\3. Country Snapshots and Profiles\2017


#Code for pulling data by Country

Sys.setenv(JAVA_HOME='C:\\Program Files (x86)\\Java\\jre1.8.0_181') # for 32-bit version
library(rJava)

#set working directory
setwd("C:/Users/Zin.Lin/OneDrive - United Nations/P_SDG_CountryProfiles")


#load RODBC and call database
library(RODBC) #load RODBC package
library(plyr)
library(dplyr)
library(data.table)
library(xlsx)
library(ggplot2)
library(psych)
library(tidyr)
library(ReporteRs)


odbcChannel <<- odbcConnect("SDGDB51")
AllDataSQL <<- paste0("select * from dbo.ObservationDn where ReleaseName = '2018.Q4.G.02'")
mydf <<- sqlQuery(odbcChannel,AllDataSQL,as.is = TRUE) 
mydata0 <<- mydf
make.names(names(mydata0))
save(mydf,file = "2018Data_20181120.RData")

Profile.Series <<- read.xlsx("C:/Users/Zin.Lin/OneDrive - United Nations/P_SDG_CountryProfiles/InputFiles/C.Profile.Conditions_20181119.xlsx",sheetName="Conditions") #create a table containing series used in country profiles
Profile.Series <<- dplyr::filter(Profile.Series,Profile.Series==1)
Profile.Series <<- dplyr::filter(Profile.Series,P.IndicatorCode != "C200203") #removing the duplicate datapoints of this multipurpose series
#IndicatorCode.2017 <<- read.xlsx("Y:/SSB/SDGs/SDG Database/2. Country Data/2017/4. Data Validation/1. Documents and Reference Files/IndicatorCode.xlsx",sheetName="IndicatorCode") #create the indicator code table
RefAreaDisaggregated_BYAREA <<- read.xlsx("Y:/SSB/SDGs/SDG Database/2. Country Data/2017/4. Data Validation/1. Documents and Reference Files/REF_AREA_DISAGGREGATED_Country_Region_World_2018.xlsx", sheetName="REF_AREA_DISAGGREGATED") #create the reference area table
#Unit_Limits <<- read.xlsx("Y:/SSB/SDGs/SDG Database/2. Country Data/2017/4. Data Validation/1. Documents and Reference Files/Unit_Upper.Lower.Limits.xlsx", sheetName = "Unit.Limits") #create a table for the upper and lower limits of unit
#Regions <<- read.xlsx("Y:/SSB/SDGs/SDG Database/2. Country Data/2017/4. Data Validation/1. Documents and Reference Files/R_Regional_Groupings.xlsx",sheetName="Sheet1") #create data file with list of regions.

#Functions
DimD <- function(){
  sqlname_dv <<- paste0("select Code, Description from dbo.DimensionValue")
  DimData <<- sqlQuery(odbcChannel,sqlname_dv,as.is = TRUE) #it shouldn't take much to load.  
  colnames(DimData)[2] <- "DimensionValueName"
  DimData1 <<- DimData
  
  sqlname_dim <<- paste0("select * from dbo.Dimension")
  Dims <<- sqlQuery(odbcChannel,sqlname_dim,as.is = TRUE) #it shouldn't take much to load.  
  colnames(Dims)[2] <- "DimensionNamSe"
  Dims1 <<- dplyr::filter(Dims,isAttribute == 0)
  Dims2 <<- Dims1[,c(2,1)]
  Dims3 <<- Dims2[!(Dims2$DimensionNamSe %in% c("Freq","Units","Reporting Type")),]
  Dims4 <<- as.array(Dims3$DimensionNamSe)
  return(Dims4)
}

save(DimData1, file = "DimData1.RData")
save(Dims4, file = "Dims4.RData")

dimid <- function(x){
  paste0(ifelse(is.na(x),"",x))
}

dimid2 <- function(x){
  tempdim <- paste0("")
  for (i in match(DimD(),names(x))) {tempdim <- paste0(tempdim,print(dimid(mydata0[,i])))}
  print(tempdim)
}
################## functions end ########################

#mydata1 <- dplyr::filter(mydata0,SeriesCode == "SI_POV_NAHC")


mydata1 <<- within(mydata0, {Dimidentifier = dimid2(mydata0)}) # produces a concatenated string of dimension values
mydata2 <<- within(mydata1, {Dimidentifierx = paste0(SeriesCode,Dimidentifier)}) # produces a concatenated string of series codes + dimension values
save(mydata2,file = "mydata2.RData")

include <- as.data.frame(unique(Profile.Series$Dimidentifierx)) # finding the unique values of Dimidentifierx
names(include) <- c("Dimidentifierx") 
mydata3 <- merge(x=include, y=mydata2, by = "Dimidentifierx", all.x = TRUE)
mydata4 <- mydata3[,colSums(is.na(mydata3))<nrow(mydata3)] #Removing blank columns

mydata <- mydata4 #renaming mydata4 to mydata

#create columns containing information about country/region disaggregations and indicator/goal information.
mydata <<- merge(x = mydata, y = RefAreaDisaggregated_BYAREA, by.x = "GeoAreaName",by.y = "M49", all.x = TRUE)
#mydata <<- merge(x = mydata, y = IndicatorCode.2017, by = "SERIES", all.x = TRUE)
# the following line creates unique series identifiers.
#mydata <<- mutate(mydata,Expr1 = paste(mydata$SERIES,mydata$SEX,mydata$AGE_GROUP,mydata$LOCATION, sep = ""))
mydata <<- merge(x = mydata, y = Profile.Series, by = "Dimidentifierx", all.x = TRUE)
#the following line creates unique row identifier for HIV series filter. Only African countries are included in the HIV series.
mydata <<- mutate(mydata,HIV.filter = paste(mydata$Dimidentifierx,mydata$AFRICA,sep = ""))
mydata <<- mutate(mydata,Zeros = paste(mydata$zero.removal,mydata$Value,sep = ""))


#profile.data <<- dplyr::filter(mydata,Profile.Series==1)
profile.data <- mydata
profile.data <<- dplyr::filter(profile.data,TimePeriod >=2000)
profile.data <<- dplyr::filter(profile.data,HIV.filter!= "SH_HIV_INCDALLAGEBOTHSEX")
zero.value.data <<- dplyr::filter(profile.data,Zeros=="10" | Zeros=="10.00000000000000") #set of not application zeros values
profile.data <<- dplyr::filter(profile.data,Zeros!="10") #data set after removal of zeros
profile.data <<- dplyr::filter(profile.data,Zeros!="10.00000000000000") #data set after removal of zeros (0.00000000000000 type)
profile.data <<- profile.data %>% drop_na(Value)

#only for 2018 exercise
profile.data$GeoAreaName[profile.data$GeoAreaName=="Sint Maarten (Dutch part)\t"]<-"Sint Maarten (Dutch part)"

#function for changing data type to numeric
num <- function(x) as.numeric(as.character(x)) #change the data type to numeric

#Function for data avialability status
#DA2 

#Main text generation function
#Variables involved: dataset,area,goalid,goalname,seriesid,texttype1,texttype2,texttype3,texttype4,texttype5

text.gen <- function(profile.data){
  for (i in unique(profile.data$GeoAreaCode)) {
    ref.data <<- dplyr::filter(profile.data,GeoAreaCode == i) #subsetting by ref.area
    ref.text <<- paste(ref.data$GeoAreaName[1])
    filename <<- paste(ref.text,".docx",sep = "")
    p.doc <<- docx()
    p.doc <<- addParagraph(p.doc,ref.text,stylename = 'PHeader')    
    for (k in sort(unique(ref.data$Goal.ID),decreasing = FALSE)){
      goal.data <<- dplyr::filter(ref.data,Goal.ID == k)
      g.text <<- paste(goal.data$Goal.Name[1])
      p.doc <<- addParagraph(p.doc,g.text,stylename = 'PGoal')
      goal.data <<- goal.data[order(goal.data$Indicator),]
      for (j in unique(goal.data$Dimidentifierx)){
        test.data <<- dplyr::filter(goal.data,Dimidentifierx == j)
        series.text<<-if(test.data$Text.type[1] == 1){text.type.1(test.data)}else
          {if(test.data$Text.type[1] == 2){text.type.2(test.data)}else
            {if(test.data$Text.type[1] == 3){text.type.3(test.data)}else
              {if(test.data$Text.type[1] == 4){text.type.4(test.data)}else
                {if(test.data$Text.type[1] == 7){text.type.7(test.data)}else
                  {if(test.data$Text.type[1] == 8){text.type.8(test.data)}else
                    {if(test.data$Text.type[1] == 9){text.type.9(test.data)}else
                      {if(test.data$Text.type[1] == 10){text.type.10(test.data)}else
                        {if(test.data$Text.type[1] == 11){text.type.11(test.data)}else
                          {if(test.data$Text.type[1] == 12){text.type.12(test.data)}else
                            {if(test.data$Text.type[1] == 13){text.type.13(test.data)}else
                              {if(test.data$Text.type[1] == 14){text.type.14(test.data)}else
                                {if(test.data$Text.type[1] == 15){text.type.15(test.data)}else
                    {"NA"}}}}}}}}}}}}}
        p.doc <<- addParagraph(p.doc,series.text,stylename = "BulletList")

        } #subsetting by series closes. test.data closes.
  
      } #subsetting by Goal closes. goal.data closes.
    p.doc <<- addParagraph(p.doc,"________________________", stylename = "PHeaderFooter")
    p.doc <<- addParagraph(p.doc,"Note (1): This fact sheet was prepared by the UN Statistics Division on selected indicators.  More data and information are available in the Sustainable Development Goal Indicators Database (http://unstats.un.org/sdgs/indicators/database/).", stylename = "PHeaderFooter")
    p.doc <<- addParagraph(p.doc,"Note (2): Some Goals may have been omitted from this profile due to a lack of data availability.", stylename = "PHeaderFooter")
    
    writeDoc(p.doc,filename)
    
    } #subsetting by ref.area closes. profile.data closes.
  
  } #function closes.

#Information about status of progress: decline/increase?#
#variables involved: dataset,min,max,textfordown,textforup
prog <<- function(test.data){
  if(num(min.obs) > num(max.obs))
  {paste(test.data$DA3.Down[1])}else
  {if(num(min.obs) < num(max.obs))
    {paste(test.data$DA3.Up[1])}else
    {NA}
    } 
}

prog.15 <<- function(test.data){
  if(num(min.obs)<0.01)
  {"nearly no coverage"}else
  {paste(profile.round(min.obs),test.data$P.Unit.Second[1],sep = "")}
}

prog.10 <<- function(test.data){
  if(num(max.obs)<10)
  {paste(test.data$DA3.Down)[1]}else
  {paste(test.data$DA3.Up)[1]}
}

prog.12 <<- function(test.data){
  if(num(max.obs)>0)
  {paste(test.data$DA3.Up)[1]}else
  {paste(test.data$DA3.Down)[1]}
}

prog.mmr.min <<- function(test.data){
  if(num(min.obs)>1)
  {" deaths"}else
  {" death"}
}

prog.mmr.max <<- function(test.data){
  if(num(max.obs)>1)
  {" deaths"}else
  {" death"}
}

#Function for "rounding in commerce" - "kaufmännische Rundung"
round2 = function(x, n) {
  posneg = sign(x)
  z = abs(x)*10^n
  z = z + 0.5
  z = trunc(z)
  z = z/10^n
  z*posneg
}



profile.round = function(x){
  if(x == ">95"|x == ">95.0"){paste("more than 95")}else #if obs value is >95, then type "greater than 95"
  {if(x == "<5"|x == "<5.0"){paste("less than 5")}else #if obs value is <5, then type "less than 5"
  {if(x == "<2.5"){paste("less than 2.5")}else #if obs value is <5, then type "less than 5"
  {if(abs(num(x)) < 0.99) {round2(num(x),2)}else #if obs value is less than 0.99, then 2 decimal points
  {if(abs(num(x)) >= 0.99 & abs(num(x)) < 10){round2(num(x),1)}else # if obs value is between 0.99 and 10, then 1 decimal point
  {if(abs(num(x)) >= 10){round2(num(x),0)}else #if obs value is greater than 10, then no decimal point
      {round(num(x),0)}}}}}}}


text.type.1 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1]," in ", min.yr, ".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
    {text <- paste(test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1]," in ", max.yr, ".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.05*abs(num(max.obs)) | num(max.obs) < .25*num(test.data$median[1]) )
    {text <- paste(test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1]," in ", max.yr, ".",sep = "")} else
  {text <- paste(test.data$DA3.1[1],prog(test.data),profile.round(min.obs),test.data$P.Unit[1]," in ",min.yr," to ",profile.round(max.obs),test.data$P.Unit[1]," in ",max.yr,".",sep = "") }
  } 
  }
  print(text)
}


text.type.2 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.1[1],".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.1[1],".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)) | num(max.obs) < num(test.data$median[1]) )
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.1[1],".",sep = "")} else
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",profile.round(max.obs),test.data$P.Unit[1],test.data$DA3.1[1],",",prog(test.data),profile.round(min.obs),test.data$P.Unit[1],"in ",min.yr,".",sep = "") }
  } 
  }
  print(text)
}



text.type.3 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.2[1],".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.2[1],".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)) | num(max.obs) < num(test.data$median[1]) )
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.2[1], ".",sep = "")} else
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.2[1],".",sep = "")}
  } 
  }
  print(text)
}

text.type.4 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs)," in ",max.yr,", meaning ",profile.round(max.obs)*100,test.data$DA2.2[1],".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs)," in ",max.yr,", meaning ",profile.round(max.obs)*100,test.data$DA2.2[1],".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)) | num(max.obs) < num(test.data$median[1]) )
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs)," in ",max.yr,", meaning ",profile.round(max.obs)*100,test.data$DA2.2[1], ".",sep = "")} else
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs)," in ",max.yr,", meaning ",profile.round(max.obs)*100,test.data$DA2.2[1],".",sep = "")}
  } 
  }
  print(text)
}


text.type.7 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1]," in ", max.yr, ".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1]," in ", max.yr,".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)) | num(max.obs) < num(test.data$median[1]) )
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1]," in ", max.yr, ".",sep = "")} else
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1]," in ", max.yr,".",sep = "")}
  } 
  }
  print(text)
}

text.type.8 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.1[1], ".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.1[1],".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)) | num(max.obs) < num(test.data$median[1]) )
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.1[1], ".",sep = "")} else
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",profile.round(max.obs),test.data$P.Unit[1],test.data$DA2.1[1],".",sep = "") }
  } 
  }
  print(text)
}

text.type.9 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)) | num(max.obs) < num(test.data$median[1]) )
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1], ".",sep = "")} else
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],", ",prog(test.data),profile.round(min.obs),test.data$P.Unit.Second[1]," in ",min.yr,".",sep = "") }
  } 
  }
  print(text)
}

text.type.10 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",prog.10(test.data),sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",prog.10(test.data),".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)) | num(max.obs) < num(test.data$median[1]) )
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",prog.10(test.data), ".",sep = "")} else
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",prog.10(test.data),".",sep = "")}
  } 
  }
  print(text)
}

text.type.11 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)) | num(max.obs) < num(test.data$median[1]) )
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1], ".",sep = "")} else
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",sep = "") }
  } 
  }
  print(text)
}



text.type.12 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  text <- paste(test.data$DA3.1[1],max.yr,", ",test.data$GeoAreaName[1],prog.12(test.data), ".",sep = "")
  
  print(text)
}

text.type.13 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs)*100,test.data$P.Unit[1],test.data$DA2.2[1],".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs)*100,test.data$P.Unit[1],test.data$DA2.2[1],".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)))
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs)*100,test.data$P.Unit[1],test.data$DA2.2[1], ".",sep = "")} else
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs)*100,test.data$P.Unit[1],test.data$DA2.2[1],".",sep = "")}
  } 
  }
  print(text)
}

text.type.14 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5" ),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs),prog.mmr.max(test.data),test.data$P.Unit[1]," in ", min.yr, ".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs),prog.mmr.max(test.data),test.data$P.Unit[1]," in ", max.yr, ".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" |  max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)) | num(max.obs) < num(test.data$median[1]) )
  {text <- paste(test.data$DA2.1[1],profile.round(max.obs),prog.mmr.max(test.data),test.data$P.Unit[1]," in ", max.yr, ".",sep = "")} else
  {text <- paste(test.data$DA3.1[1],prog(test.data),profile.round(min.obs),prog.mmr.min(test.data),test.data$P.Unit[1]," in ",min.yr," to ",profile.round(max.obs),prog.mmr.max(test.data),test.data$P.Unit[1]," in ",max.yr,".",sep = "") }
  } 
  }
  print(text)
}

text.type.15 <<- function(test.data){
  n.yr <<- length(test.data$TimePeriod)
  min.yr <<- min(test.data$TimePeriod)
  max.yr <<- max(test.data$TimePeriod)
  min.yr.data <<- dplyr::filter(test.data,TimePeriod == min.yr)
  min.obs <<- min.yr.data$Value
  max.yr.data <<- dplyr::filter(test.data,TimePeriod == max.yr)
  max.obs <<- max.yr.data$Value
  dif.obs <<- ifelse((max.obs == ">95" | max.obs == "<5" | min.obs == "<5" | max.obs == "2.5" | min.obs=="2.5"),0,abs(num(max.obs)-num(min.obs)))
  
  if(n.yr==1)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",sep = "")} else
  {if(n.yr>1 & min.yr>=2010)
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],".",sep = "")} else
  {if(min.obs == max.obs | max.obs == ">95" | max.obs == "<5" | max.obs == "<2.5" | min.obs == "2.5"| dif.obs < 0.01*abs(num(max.obs)) | num(max.obs) < num(test.data$median[1]) )
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1], ".",sep = "")} else
  {text <- paste(test.data$T.CapIn[1],max.yr,", ",test.data$DA2.1[1],profile.round(max.obs),test.data$P.Unit[1],",",prog(test.data),prog.15(test.data)," in ",min.yr,".",sep = "") }
  } 
  }
  print(text)
}

text.gen(profile.data)

################################################### Country profile generation program ends.


write.csv(profile.data,"profile.data.csv")



