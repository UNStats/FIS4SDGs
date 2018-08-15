#devtools::install_github("gluc/data.tree")
library(data.tree)
library(jsonlite)
library(magrittr)

setwd("C:/Users/L.GonzalezMorales/Documents/GitHub/sdg-publisher/FIS4SDG")

series.tags <- read.table("reference_tables//SeriesCatalogTagging.txt", 
                          header = TRUE, 
                          sep = "\t", 
                          quote = "",
                          na.strings = "", 
                          comment.char = "",
                          stringsAsFactors = FALSE)

currentRelease <- "2018.Q2.G.01"

series.tags.current <- series.tags[series.tags$seriesRelease == "2018.Q2.G.01",]

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
