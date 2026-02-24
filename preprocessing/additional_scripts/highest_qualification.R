# Choose the highest qualification

```{r}
qual_cols <- grep("^qualification\\.", names(ukb_v2), value = TRUE)
rank_map <- c(
  "None of the above" = 1,
  "CSEs or equivalent" = 2,
  "O levels/GCSEs or equivalent" = 3,
  "A levels/AS levels or equivalent" = 4,
  "NVQ or HND or HNC or equivalent" = 5,
  "Other professional qualifications eg: nursing, teaching" = 5,
  "College or University degree" = 6
)
clean_txt <- function(z) {
  z <- as.character(z)
  z <- trimws(z)                 
  z <- gsub("\\s+", " ", z)     
  z
}
rank_map_clean <- rank_map
names(rank_map_clean) <- clean_txt(names(rank_map_clean))

ukb_v2 <- ukb_v2 %>%
  mutate(qualification_highest = apply(select(ukb_v2, all_of(qual_cols)), 1, function(x) {
    
    x <- clean_txt(x)
    x <- x[!is.na(x) & x != "" & x != "Prefer not to answer"]
    if (length(x) == 0) return(NA_character_)
    
    scores <- unname(rank_map_clean[x])
    if (all(is.na(scores))) return(NA_character_)
    
    scores2 <- ifelse(is.na(scores), -Inf, scores)
    x[which.max(scores2)] 
  }))

ukb_v2$qualification_highest <- as.factor(ukb_v2$qualification_highest)

ukb_v2 <- ukb_v2[, !grepl("qualification\\.0\\.[0-5]$", names(ukb_v2))]
#keep the latest status
```
