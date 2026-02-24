
# Use 5 sleep factors: 
  # "sleep_daytime_dozing.0.0" <- "Sometimes", "Often", "All of the time" ~ 1, "Never/rarely" ~ 0
  # "sleep_insomnia.0.0" <- "Sometimes", "Usually" ~ 1, "Never/rarely" ~ 0
  # "sleep_snore.0.0" <- "Yes" ~ 1, "No" ~ 0
  # "sleep_chronotype.0.0" <- "More an 'evening' than a 'morning' person" | "Definitely an 'evening' person" ~ 1, "Definitely a 'morning' person" | "More a 'morning' than 'evening' person" ~ 0
  # "sleep_duration.0.0" <- <7 | > 8 ~ 1, >=7 | <=8  ~ 0

library(dplyr)

# subscore 1: sleep duration (<7 or >8 hours = unhealthy)

ukb_v3 <- ukb_v3 %>%
  mutate(sleep_duration_score = case_when(
      sleep_duration.0.0 < 7 ~ 1,
      sleep_duration.0.0 > 8 ~ 1,
      sleep_duration.0.0 >= 7 & sleep_duration.0.0 <= 8 ~ 0,
      TRUE ~ NA_real_),
    
    # subscore 2: Chronotype (evening types = unhealthy)
    sleep_chronotype_score = case_when(
      sleep_chronotype.0.0 %in% c("More an 'evening' than a 'morning' person", "Definitely an 'evening' person") ~ 1,
      sleep_chronotype.0.0 %in% c("Definitely a 'morning' person", "More a 'morning' than 'evening' person") ~ 0,
      TRUE ~ NA_real_
    ),
    
    # subscore 3: Insomnia (sometimes or usually = unhealthy)
    sleep_insomnia_score = case_when(
      sleep_insomnia.0.0 %in% c("Sometimes", "Usually") ~ 1,
      sleep_insomnia.0.0 == "Never/rarely" ~ 0,
      TRUE ~ NA_real_
    ),
    
    # subscore 4: Snoring (Yes = unhealthy)
    sleep_snore_score = case_when(
      sleep_snore.0.0 == "Yes" ~ 1,
      sleep_snore.0.0 == "No" ~ 0,
      TRUE ~ NA_real_
    ),
    
    # subscore 5: Daytime sleepiness (sometimes or usually = unhealthy)
    sleep_daytime_score = case_when(
      sleep_daytime_dozing.0.0 %in% c("Sometimes", "Often", "All of the time") ~ 1,
      sleep_daytime_dozing.0.0 == "Never/rarely" ~ 0,
      TRUE ~ NA_real_
    )
  )

# Accumulated sleep_score (ranges from 0 to 5 <-5 is most unhealthy sleep score, 0 is healthy sleep score)

ukb_v3 <- ukb_v3 %>%
  mutate(
    sleep_score = sleep_duration_score +
      sleep_chronotype_score +
      sleep_insomnia_score +
      sleep_snore_score +
      sleep_daytime_score
  )

# categorise overall sleep patterns into: 
  # healthy (sleep score 0–1)
  # intermediate (sleep score 2–3)
  # poor (sleep score 4–5) 

ukb_v3 <- ukb_v3 %>%
  mutate(
    sleep_category = case_when(
      sleep_score %in% 0:1 ~ "Healthy",
      sleep_score %in% 2:3 ~ "Intermediate",
      sleep_score %in% 4:5 ~ "Poor",
      TRUE ~ NA_character_
    )
  )

# made ordered factor for down the line analysis

ukb_v3$sleep_category <- factor(
  ukb_v3$sleep_category,
  levels = c("Healthy", "Intermediate", "Poor"),
  ordered = TRUE
)

# check the distribution of sleep scores

library(ggplot2)

ggplot(ukb_v3, aes(x = sleep_score)) +
  geom_histogram(
    binwidth = 1,
    boundary = -0.5,   # aligns bins to 0,1,2,3,4,5
    na.rm = TRUE
  ) +
  scale_x_continuous(breaks = 0:5) +
  labs(
    title = "Distribution of Sleep Score",
    x = "Sleep Score (0 = Healthiest, 5 = Unhealthiest)",
    y = "Count"
  ) +
  theme_minimal()

# check the distribution of sleep categories 

ggplot(ukb_v3, aes(x = sleep_category)) +
  geom_bar(na.rm = TRUE, fill = "steelblue") +
  labs(
    title = "Distribution of Sleep Categories",
    x = "Sleep Category",
    y = "Count"
  ) +
  theme_minimal()