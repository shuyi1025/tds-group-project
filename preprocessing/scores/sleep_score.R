# reproducible sleep score script

# Use 5 sleep factors: 
# "sleep_daytime_dozing.0.0" <- "Sometimes", "Often", "All of the time" ~ 1, "Never/rarely" ~ 0
# "sleep_insomnia.0.0" <- "Sometimes", "Usually" ~ 1, "Never/rarely" ~ 0
# "sleep_snore.0.0" <- "Yes" ~ 1, "No" ~ 0 
# "sleep_chronotype.0.0" <- "More an 'evening' than a 'morning' person" | "Definitely an 'evening' person" ~ 1, "Definitely a 'morning' person" | "More a 'morning' than 'evening' person" ~ 0
# "sleep_duration.0.0" <- <7 | > 8 ~ 1, >=7 | <=8  ~ 0

library(dplyr)

# create a function to remove the need to rerun the script

create_sleep_score <- function(df) {
  
  df %>%
    mutate(
     
       # Sleep duration (<7 or >8 hours = unhealthy)
      sleep_duration_score = case_when(
        sleep_duration.0.0 < 7 ~ 1,
        sleep_duration.0.0 > 8 ~ 1,
        sleep_duration.0.0 >= 7 & sleep_duration.0.0 <= 8 ~ 0,
        TRUE ~ NA_real_
      ),
      
      #  Chronotype (evening types = unhealthy)
      sleep_chronotype_score = case_when(
        sleep_chronotype.0.0 %in% c(
          "More an 'evening' than a 'morning' person",
          "Definitely an 'evening' person"
        ) ~ 1,
        sleep_chronotype.0.0 %in% c(
          "Definitely a 'morning' person",
          "More a 'morning' than 'evening' person"
        ) ~ 0,
        TRUE ~ NA_real_
      ),
      
      # Insomnia (sometimes or usually = unhealthy)
      sleep_insomnia_score = case_when(
        sleep_insomnia.0.0 %in% c("Sometimes", "Usually") ~ 1,
        sleep_insomnia.0.0 == "Never/rarely" ~ 0,
        TRUE ~ NA_real_
      ),
      
      # Snoring (Yes = unhealthy)
      sleep_snore_score = case_when(
        sleep_snore.0.0 == "Yes" ~ 1,
        sleep_snore.0.0 == "No" ~ 0,
        TRUE ~ NA_real_
      ),
      
      # Daytime sleepiness (sometimes or usually = unhealthy)
      sleep_daytime_score = case_when(
        sleep_daytime_dozing.0.0 %in% c("Sometimes", "Often", "All of the time") ~ 1,
        sleep_daytime_dozing.0.0 == "Never/rarely" ~ 0,
        TRUE ~ NA_real_
      ),
      
      # Total score
      sleep_score = sleep_duration_score +
        sleep_chronotype_score +
        sleep_insomnia_score +
        sleep_daytime_score +
        sleep_snore_score,
      
      # Category - for better interpretation of score
      sleep_category = case_when(
        sleep_score %in% 0:1 ~ "Healthy",
        sleep_score %in% 2:3 ~ "Intermediate",
        sleep_score %in% 4:5 ~ "Poor",
        TRUE ~ NA_character_
      )
    ) %>%
    
    # Remove intermediate variables
    select(
      -sleep_chronotype.0.0,
      -sleep_daytime_dozing.0.0,
      -sleep_duration.0.0,
      -sleep_insomnia.0.0,
      -sleep_snore.0.0,
      -sleep_chronotype_score,
      -sleep_daytime_score,
      -sleep_duration_score,
      -sleep_insomnia_score,
      -sleep_snore_score,
      -sleep_score
    ) %>%
    
    # Ordered factor
    mutate(
      sleep_category = factor(
        sleep_category,
        levels = c("Healthy", "Intermediate", "Poor"),
        ordered = TRUE
      )
    )
}

# Run on train and test set

ukb_train <- create_sleep_score(ukb_train)
ukb_test  <- create_sleep_score(ukb_test)



