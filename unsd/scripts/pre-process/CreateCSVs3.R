
#------------------------------------------------------------------------------
library(jsonlite)
library(tidyr)
library(data.table)
library(rapportools)


setwd("C:/Users/L.GonzalezMorales/Documents/GitHub/FIS4SDGs/unsd")

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
for(g in 1:1)
  #for(i in 1:nSeries)
{

  totalElements <- fromJSON(paste("https://unstats.un.org/SDGAPI/v1/sdg/Goal/Data?goal=",g,"&pageSize=2",sep=""))$totalElements
  

  pageSize = 500
  nPages = totalElements %/% pageSize + 1
  
  cat("g = ",  g, "; totalElements = ", totalElements, "; pageSize = ", pageSize, "; Pages = ", nPages,"\n")
  
  if(totalElements>1)
  {
    for(p in 1:nPages){
      
      queryString <- paste("https://unstats.un.org/SDGAPI/v1/sdg/Goal/Data?goal=",g,"&page=",p,"&pageSize=",pageSize,sep="")
      
      p.x     <- readPage(queryString )
      p.slice <- as.data.table(unlist(unique(p.x$data$dimensions)))
  
      
      
      # Extract data matrix:
      p.data <- p.x$data[,c("goal",
                            "target",
                            "indicator",
                            "series",
                            "seriesDescription",
                            "geoAreaCode",
                            "timePeriodStart",
                            "value",
                            "time_detail",
                            "source")]
      colnames(p.data)[colnames(p.data)=="timePeriodStart"] <- "years"
      
      # Need to select unique records for the case of multi-indicator series:
      p.data <- unique(cbind(p.data, p.x$data$dimensions, p.x$data$attributes))
      p.data$value <- as.numeric(p.data$value)
      
      for(i in 1:length(names(p.data)))
      {
        
        z <- rep(NA,length(p.data[,i]))
        
        for(j in 1:length(p.data[,i])){
          
          x <- p.data[,i][[j]]
          
          if(i == 1){
            
            z[j] <- x[x==g]
            
          } else if(i == 2){
            
            z[j] <- x[gsub( "[.].*$", "", x )==g]
            
          } else if(i == 3){
            
            z[j] <- x[gsub( "[.].*$", "", x )==g]
            
          } else {
            
            z[j] <- x
            
          }
        
        }
        
        p.data[,i] <- z
        
      }
      
      if(p == 1)
      {
        
        data <- p.data
        slice <- p.slice
        
      } else {
        
        data <- rbindlist(list(data,p.data), fill = TRUE)
        slice <- unique(rbindlist(list(slice,p.slice), fill = TRUE))

      }
      
      cat("      Processing page ", p, " of ", nPages, "\n")
      
    }
    
    
    #dimensions
    dimensions.data <- !names(data) %in% c("goal",
                                           "target",
                                           "indicator",
                                           "series",
                                           "seriesDescription",
                                           "geoAreaCode" ,
                                           "years",
                                           "value",
                                           "time_detail",
                                           "source",
                                           "Nature",
                                           "Units",
                                           "UnitMultiplier")
    
    dimensions <- names(data)[dimensions.data]
    data <- data[,N :=length(years), by =   c("series", "geoAreaCode", dimensions)]
    
    latest.data <- setDT(data)[,.SD[which.max(years)], 
                               by =  c("series", "geoAreaCode", dimensions)]
    setnames(latest.data, old = "years", new = "latest.year")
    setnames(latest.data, old = "value", new = "latest.value")
    
    data <- merge(data, latest.data)
    
    data[,geoAreaCode := as.integer(geoAreaCode)]
    
    #===================================================================
    # Pivot matrix
    #===================================================================
  
    
    data.pivot <- data %>% 
      gather(key, value, c(value,  source, time_detail, Nature))
    
    data.pivot <- data.pivot %>%
      unite(temp1, years, key, sep = ".")
    
    data.pivot <- data.pivot[,! names(data.pivot) %in% c( "years")] %>%
      spread(temp1, value)
    
    data.pivot <- as.data.table(data.pivot)
    data.pivot[,geoAreaCode := as.integer(geoAreaCode)]
    
    
    #===================================================================
    # Build grid
    #===================================================================
    
    
    # Create grid of key columns
    
    geoAreaCodes  <- countryListXY$geoAreaCode
    
    seriesBlock   <- unique(data[, list(goal,
                                     target,
                                     indicator,
                                     series,
                                     seriesDescription,
                                     Units,
                                     UnitMultiplier)])
    
    seriesCodes   <- seriesBlock$series
    
    sliceColumns <- names(data)[!names(data)%in%c("geoAreaCode",
                                                  "valueType",
                                                  "time_detail",
                                                  "source",
                                                  "Nature",
                                                  "N",
                                                  "years",
                                                  "value",
                                                  "latest.year",
                                                  "latest.value")]
    
     sliceBlock <-  unique(data[, ..sliceColumns, with = TRUE])
     
     sliceBlock[, sliceId := seq_len(.N), by = "series" ]
     sliceBlock[, sliceBlockId := .I ]
     
     # cross-join:
     grid.table <- CJ(sliceBlockId=sliceBlock$sliceBlockId,geoAreaCode=countryListXY$geoAreaCode)
     
     data.full <- merge(merge(grid.table, sliceBlock, by = "sliceBlockId"), countryListXY, by ="geoAreaCode")
     
     
     data.full <- merge(data.full, data.pivot, by = names(data.full)[names(data.full) %in% names(data.pivot)], all.x= TRUE)
     
     #===================================================================
     # Unpivot full table
     #===================================================================
     
     pivot.columns <- c(paste(unique(data[,years]), "Nature", sep = "."),
                        paste(unique(data[,years]), "source", sep = "."),
                        paste(unique(data[,years]), "time_detail", sep = "."),
                        paste(unique(data[,years]), "value", sep = "."))
     
     data.full.long <- data.full %>% gather(Year.Variable, Value, pivot.columns)
     
     data.full.long <- as.data.table(data.full.long %>% separate(Year.Variable, c("Year", "Variable"), sep = "\\."))
     
     data.n <- data.full.long[data.full.long$Variable =="Nature",]
     setnames(data.n,"Value","Nature")
     data.n[,Variable := NULL]
     
     data.s <- data.full.long[data.full.long$Variable =="source",]
     setnames(data.s,"Value","source")
     data.s[,Variable := NULL]
     
     data.td <- data.full.long[data.full.long$Variable =="time_detail",]
     setnames(data.td,"Value","time_detail")
     data.td[,Variable := NULL]
     
     data.v <- data.full.long[data.full.long$Variable =="value",]
     setnames(data.v,"Value","value")
     data.v[,Variable := NULL]
     
     data.full.long2 <- merge(merge(merge(data.n, data.s),data.td),data.v)
     
     data.full.long2[latest.year == Year,isLatestYear := TRUE]
     data.full.long2[,latest.year := NULL]
     data.full.long2[,latest.value := NULL]
     
     names(data.full.long2)
     
     setcolorder(data.full.long2, c("goal",
                                    "target",
                                    "indicator",
                                    "series",
                                    "seriesDescription",
                                    "X",
                                    "Y",
                                    "geoAreaCode",
                                    "geoAreaName",
                                    "ISO3CD",
                                    "Year",
                                    dimensions,
                                    "Units",
                                    "UnitMultiplier",
                                    "Nature",
                                    "source",
                                    "time_detail",
                                    "value",
                                    "isLatestYear",
                                    "N",
                                    "sliceBlockId",
                                    "sliceId"
                                    ))
     
     
     
     
    #===================================================================
    # Convert column titles to CamelCase
    #===================================================================
     
    setnames(data.full.long2,names(data.full.long2),tocamel(names(data.full.long2), upper = TRUE))
    setnames(data.full.long2,"Value", "ObsValue")
     names(data.full.long2)
    
    
    #===================================================================
    # write to tab-delimited file
    #===================================================================

    write.table( data.pivot,
                file = paste("country-profiles/data/csv/goal",g,"_pivot.csv", sep=""),
                append = FALSE,
                quote = FALSE,
                sep = "\t",
                eol = "\n",
                na = "",
                dec = ".",
                row.names = FALSE,
                col.names = TRUE,
                fileEncoding = "UTF-8")

# 
#      write.table( data.full.long2 ,
#                   file = paste("country-profiles/data/csv/goal",g,"_full_long.csv", sep=""),
#                   append = FALSE,
#                   quote = FALSE,
#                   sep = "\t",
#                   eol = "\n",
#                   na = "",
#                   dec = ".",
#                   row.names = FALSE,
#                   col.names = TRUE,
#                   fileEncoding = "UTF-8")
     
     
     write.table( data.full.long2[!is.na(data.full.long2$ObsValue),] ,
                  file = paste("country-profiles/data/csv/goal",g,"_dense_long.csv", sep=""),
                  append = FALSE,
                  quote = FALSE,
                  sep = "\t",
                  eol = "\n",
                  na = "",
                  dec = ".",
                  row.names = FALSE,
                  col.names = TRUE,
                  fileEncoding = "UTF-8")
      
  }
}
