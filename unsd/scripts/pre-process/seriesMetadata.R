###############################################################################
# Use this code to produce a "denormalized" SDG Metadata json file
###############################################################################

library(jsonlite)
library(tidyr)
library(data.table)
library(readr)

################################################################################

currentRelease <- "2018.Q2.G.01"

setwd("C:/Users/L.GonzalezMorales/Documents/GitHub/sdg-publisher/FIS4SDG")

################################################################################

goalMetadata <- read.table("reference_tables//goalMetadata.txt", 
                           header = TRUE, 
                           sep = "\t", 
                           as.is = TRUE,
                           na.strings = "", 
                           encoding = "UTF-8")

goalColorScheme <- read.table("reference_tables//sdgColorScheme.txt", 
                              header = TRUE, 
                              sep = "\t", 
                              as.is = TRUE,
                              na.strings = "", 
                              encoding = "UTF-8")

goalMetadata2 <- merge(goalMetadata,
                       goalColorScheme,
                       by.x = "goal",
                       by.y = "Goal")

names(goalMetadata2)[6] <- "ColorSchemeCredits"


goalMetadata2$rgb <-  lapply(strsplit(goalMetadata2$rgb, ","), trimws)
goalMetadata2$rgb <-  lapply(goalMetadata2$rgb, as.numeric)

goalMetadata2$ColorScheme <-  lapply(strsplit(goalMetadata2$ColorScheme, ","), trimws)

# See: https://blog.exploratory.io/saving-the-data-to-json-file-1dedb8d31a37

goalMetadata2 %>% 
  toJSON() %>%
  write_lines("json//goalMetadata.json")


#--------------------------------------------------------

series.tags <- read.table("reference_tables//SeriesCatalogTagging.txt", 
                          header = TRUE, 
                          sep = "\t", 
                          quote = "",
                          na.strings = "", 
                          comment.char = "",
                          stringsAsFactors = FALSE)


series.tags.current <- series.tags[series.tags$seriesRelease == currentRelease,]

series.tags.current$TAGS <- lapply(strsplit(series.tags.current$TAGS, ","), trimws)

#---------------------------------------------------

seriesMetadata <- merge(series.tags.current, goalMetadata2,
                          by.x = "goalCode",
                          by.y = "goal",
                          all.x = TRUE)


##########################################################################

# See: https://blog.exploratory.io/saving-the-data-to-json-file-1dedb8d31a37

seriesMetadata %>% 
  toJSON() %>%
  write_lines("json//seriesMetadata.json")

##########################################################################



