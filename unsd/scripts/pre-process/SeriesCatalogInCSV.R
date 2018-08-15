#devtools::install_github("gluc/data.tree")
library(data.tree)
library(jsonlite)
library(magrittr)

setwd("C:/Users/L.GonzalezMorales/Documents/GitHub/sdg-publisher/FIS4SDG")


GoalsList <- fromJSON("https://unstats.un.org/SDGAPI/v1/sdg/Goal/List?includechildren=true", simplifyDataFrame = FALSE)
goals <- as.Node(GoalsList)

# print(goals, "code", "title", "description", "release")


#convert this to a data.frame
seriesDF <- goals %>% ToDataFrameTable(
                                    goalCode = function(x) x$parent$parent$parent$parent$parent$code,
                                    goalTitle = function(x) x$parent$parent$parent$parent$parent$title,
                                    targetCode = function(x) x$parent$parent$parent$code,
                                    targetTitle = function(x) x$parent$parent$parent$title,
                                    indicatorCode = function(x) x$parent$code, #relative to the leaf
                                    indicatorDescription = function(x) x$parent$description,
                                    seriesCode = "code", 
                                    seriesDescription="description",
                                    seriesRelease = "release",
                                    level = function(x) x$level
                                   )

seriesDF <- seriesDF[seriesDF$level == 8,]

seriesDF <- subset(seriesDF, select = -c(level))

write(toJSON(setNames(seriesDF,names(seriesDF))),
      file = "json//SeriesCatalog.json")


write.table(seriesDF, 
            file = "reference_tables//SeriesCatalog_allReleases.csv", 
            append = FALSE,
            sep = "\t",
            eol = "\n", 
            na = "", 
            dec = ".", 
            row.names = FALSE,
            col.names = TRUE, 
            fileEncoding = "UTF-8")
