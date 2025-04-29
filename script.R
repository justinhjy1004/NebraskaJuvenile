library(tidyverse)
library(lubridate)

## Fiscal Year
get_fiscal_year <- function(date) {
  year_part <- year(date)
  fiscal_year <- if_else(month(date) >= 7, year_part + 1, year_part)
  return(fiscal_year)
}

df <- read_csv("./Data/JuvenileCaseInfo.csv") |>
  mutate(Year = get_fiscal_year(mdy(FiledDate))) |>
  group_by(Classification, County, Year) |>
  summarize( count = n())

scone <- read_csv("./Data/SCONE.csv") |>
  gather(key = "Classification", value = "count", 3:5) |>
  mutate(Source = "SCONE")

df |>
  mutate( Source = "NE Justice" ) |>
  filter(Classification != "Traffic Offense" ) |>
  filter(Classification != "Dependency") |>
  rbind(scone)  -> df

ggplot(df, aes( x = Year, y = count, color = Classification)) +
  geom_point(aes(shape = Source)) +
  geom_line(aes(linetype = Source)) +
  facet_wrap(~ County + Classification, scales = "free_y") +
  theme_classic() +
  theme(legend.position = "top") +
  ylab("Count") +
  scale_x_continuous(breaks=seq(2010,2024,3))

ggsave("SCONE_v_NE_Justice.png", device = "png", width = 9, height = 5)

df |>
  spread(key = "Source", value = "count") |>
  drop_na() |>
  mutate(Difference = SCONE - `NE Justice`)-> d_diff


ggplot(d_diff, aes( x = Year, y = Difference, color = Classification)) +
  geom_point() +
  geom_line() +
  facet_wrap(~ County + Classification, scales = "free_y") +
  theme_classic() +
  theme(legend.position = "top") +
  scale_x_continuous(breaks=seq(2015,2024,3))

ggsave("SCONE_v_NE_Justice_Difference.png", device = "png", width = 9, height = 5)
