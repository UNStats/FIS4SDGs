#devtools::install_github("gluc/data.tree")
library(data.tree)
library(jsonlite)
library(magrittr)

##https://cran.r-project.org/web/packages/data.tree/vignettes/data.tree.html

setwd("C:/Users/L.GonzalezMorales/Documents/GitHub/sdg-publisher/FIS4SDG")


GoalMetadata<- fromJSON("https://raw.githubusercontent.com/UNStats-SDGs/sdg-publisher/master/FIS4SDG/metadataAPI.json", simplifyDataFrame = FALSE)
goalMetadata <- as.Node(GoalMetadata)

print(goalMetadata, "hex", "rgb", "icon_url_sq")
# print(goals, "code", "title", "description", "release")


#convert this to a data.frame
goalMetadataDF <- goalMetadata %>% ToDataFrameTable(
                                    "goal",
                                    icon_url_sq = function(x) x$parent$icon_url_sq,
                                    "hex", 
                                    "rgb",
                                    level = function(x) x$level
                                   )

goalMetadataDF <- goalMetadataDF[goalMetadataDF$level == 3,c("goal", "hex", "rgb", "icon_url_sq")]

write.table(goalMetadataDF, 
            file = "goalsMetadata.txt", 
            append = FALSE,
            sep = "\t",
            eol = "\n", 
            na = "", 
            dec = ".", 
            row.names = FALSE,
            col.names = TRUE, 
            fileEncoding = "UTF-8")
