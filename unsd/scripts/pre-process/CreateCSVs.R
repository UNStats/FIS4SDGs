
#------------------------------------------------------------------------------
library(jsonlite)
library(tidyr)
library(data.table)


setwd("C:/Users/L.GonzalezMorales/Documents/GitHub/sdg-publisher/FIS4SDG")


#-----------------------------------------------------------------------------
# List of countreis to be plotted on a map (with XY coordinates)
#------------------------------------------- ----------------------------------

countryListXY <- as.data.frame(read.table("CountryListXY.txt", 
                                          header = TRUE, 
                                          sep = "\t",
                                          quote = "",
                                          na.strings = "", 
                                          stringsAsFactors = FALSE,
                                          encoding = "UTF-8"))

countryListXY[countryListXY$geoAreaCode==248,"geoAreaName"] <- "Åland Islands"
countryListXY[countryListXY$geoAreaCode==384,"geoAreaName"] <- "Côte d'Ivoire"
countryListXY[countryListXY$geoAreaCode==531,"geoAreaName"] <- "Curaçao"
countryListXY[countryListXY$geoAreaCode==638,"geoAreaName"] <- "Réunion"
countryListXY[countryListXY$geoAreaCode==652,"geoAreaName"] <- "Saint Barthélemy"

#------------------------------------------------------------------------------
# List of al series available 

SeriesList  <- as.data.table(fromJSON("https://unstats.un.org/SDGAPI/v1/sdg/Series/List?allreleases=false"))[,c("release","code","description")]
nSeries <- length(SeriesList[[2]])

xx <- which(SeriesList$code == 'EN_MAT_FTPRTN')

readPage <- function(queryString) {
  out <- tryCatch(
    {
      message("This is the 'try' part")
      fromJSON(queryString) 
    },
    error=function(cond) {
      message(paste("Something went terribly wrong with request: ", queryString ))
      message("Here's the original error message:")
      message(cond)
      # Choose a return value in case of error
      return(NULL)
    },
    warning=function(cond) {
      message(paste("Request caused a warning:", queryString))
      message("Here's the original warning message:")
      message(paste(cond, "\n"))
      
      # Choose a return value in case of warning
      return(NULL)
    },
    finally={
      message(paste("Processed request:", queryString))
      message("cool!")
      
    }
  )    
  return(out)
}

#------------------------------------------------------------------------------
# Pull data for each series
#------------------------------------------------------------------------------
for(i in xx:xx)
#for(i in 1:nSeries)
{
    seriesRelease <- SeriesList[i][[1]]
    #seriesRelease <- "2018.Q2.G.01"
    
    series <- SeriesList[i][[2]]
    #series <- "VC_VAW_DIST"
    
    seriesDesc <- SeriesList[i][[3]]
    #seriesDesc <- "Age and sex distribution of detected victims of trafficking in persons (%)"
    
    totalElements <- fromJSON(paste("https://unstats.un.org/SDGAPI/v1/sdg/Series/Data?seriesCode=",series,"&pageSize=2",sep=""))$totalElements
   
    pageSize = 500
    nPages = totalElements %/% pageSize + 1
    
    cat("i = ",  i, "; totalElements = ", totalElements, "; pageSize = ", pageSize, "; Pages = ", nPages,"\n")

    if(totalElements>1)
    {
        for(p in 1:nPages){
          
          queryString <- paste("https://unstats.un.org/SDGAPI/v1/sdg/Series/Data?seriesCode=",series,"&page=",p,"&pageSize=",pageSize,sep="")
          
          p.x     <- readPage(queryString )
          p.slice <- unique(p.x$data$dimensions)
          
          
          # Extract data matrix:
          p.data <- p.x$data[,c("geoAreaCode",
                                "timePeriodStart",
                                "value",
                                "valueType",
                                "time_detail",
                                "source")]
          colnames(p.data)[colnames(p.data)=="timePeriodStart"] <- "years"
          # Need to select unique records for the case of multi-indicator series:
          p.data <- unique(cbind(p.data, p.x$data$dimensions, p.x$data$attributes))
          p.data$value <- as.numeric(p.data$value)
          
          if(p == 1)
          {
            
            data <- p.data
            slice <- p.slice
              
          } else {
            
            data <- rbind(data, p.data) 
            slice <- unique(rbind(slice,p.slice))
            
            
          }
          
          cat("      Processing page ", p, " of ", nPages, "\n")
          
        }
      
        # Create grid of key columns
        geoAreaCodes  <- countryListXY$geoAreaCode
        slice$sliceId <- 1:nrow(slice)
        years         <- unique(data$years)
        
        grid <- expand.grid(geoAreaCode = geoAreaCodes, 
                            sliceId = slice$sliceId, 
                            years = years)
        
        grid$series.release <- seriesRelease
        grid$series.code <- series
        grid$series.description <- seriesDesc

        
        if(sum(data$geoAreaCode %in% geoAreaCodes)>0){
          
          
          # Create data cube by left-joining grid and data matrix:
          cube <- merge(merge(merge(grid,
                                    countryListXY,
                                    all.x = TRUE),
                              slice,
                              all.x = TRUE),
                        data,
                        all.x = TRUE)
          
          cube <- cube[order(cube$geoAreaCode, cube$sliceId, cube$years),]
          
          if(nrow(cube) > nrow(unique(cube))){
            cat(      "(!) Has duplicates: ", series, "-", seriesDesc,"\n")
            cube <- unique(cube)
          }
          
          for(d in 1:length(p.x$dimensions[[1]])){
            
            lookup.d <- as.data.table(p.x$dimensions[[2]][d])[, list(code, description)]
            setnames(lookup.d, c("code",paste(p.x$dimensions[[1]][d], "description", sep = " ")) )
            
            if(p.x$dimensions[[1]][d] %in% names(cube)) {
              cube <- merge(cube,
                            lookup.d, 
                            by.x = p.x$dimensions[[1]][d], 
                            by.y = "code", 
                            all.x = TRUE)
            }
            
 
          }

          
          
          
          columns.Long <- c("series.release", "series.code","series.description","geoAreaCode","X", "Y", "ISO3CD", "geoAreaName", "sliceId",
                            p.x$dimensions[[1]], paste(p.x$dimensions[[1]], "description", sep=" "), "years", "value",
                             "valueType","time_detail","source","Nature")
          
          cube <- cube[,columns.Long[columns.Long %in% names(cube)]]
          
          setcolorder(cube, columns.Long[columns.Long %in% names(cube)] )
          #-------------------------------------------
          # Generate cube pivot
          #-------------------------------------------
          dimNames <- names(p.x$data$dimensions)[names(p.x$data$dimensions)%in%names(cube)]
          
          paste(dimNames, "description", sep=" ")
          
          columns <- c("series.release", "series.code","series.description","geoAreaCode","X", "Y", "ISO3CD", "geoAreaName", "sliceId",
                       dimNames, paste(dimNames, "description", sep=" "), "years", "value")
          
          
          
          cube.pivot <- cube[,columns] 
          cube.pivot <-  cube[,columns]  %>% spread(years,value)
          
          last.year <- max(cube[,"years"])
          
          
          last.5.years <- names(cube.pivot) %in% as.character(seq(last.year-4,last.year,1))
          
          if(sum(last.5.years)>1)  {
            cube.pivot$last.5.years.mean <- apply(cube.pivot[,last.5.years],1,mean, na.rm=TRUE)
          } 
          
          
          cube <- as.data.table(cube)
          cube.latest <- cube[cube[!is.na(value), .I[years == max(years)], by =  c("geoAreaCode", "sliceId")]$V1]
          
          names(cube.latest)
          
          cube.latest <- cube.latest[,-c("OBJECTID", "valueType", "time_detail"),  with=FALSE]
          setnames(cube.latest, old = "years", new = "latest.year")
          setnames(cube.latest, old = "value", new = "latest.value")
          setnames(cube.latest, old = "source", new = "latest.source")
          if("Nature" %in% names(cube.latest))
            {
            setnames(cube.latest, old = "Nature", new = "latest.nature")  
          }
          
          
          cube.pivot <- merge(cube.pivot, cube.latest, all.x = TRUE)      
      
          write.table(cube, 
                      file = paste("csv/",series,"_cube.csv", sep=""), 
                       append = FALSE,
                       quote = FALSE, 
                       sep = "\t",
                       eol = "\n", 
                       na = "", 
                       dec = ".", 
                       row.names = FALSE,
                       col.names = TRUE, 
                       fileEncoding = "UTF-8")
          
               
          write.table(cube.pivot, 
                      file = paste("csv/",series,"_cube.pivot.csv", sep=""), 
                      append = FALSE,
                      quote = FALSE, 
                      sep = "\t",
                      eol = "\n", 
                      na = "", 
                      dec = ".", 
                      row.names = FALSE,
                      col.names = TRUE, 
                      fileEncoding = "UTF-8")
          
          
         
          cat("finished ", i, "of ", nSeries, "\n")
        }
    }
}
