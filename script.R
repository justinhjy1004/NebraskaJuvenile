library(tidyverse)

df <- read_csv("Counts.csv")

ezaco <- read_csv("EZACO.csv") |>
  gather( key = "Classification", value = "count", 3:5) |>
  drop_na() |>
  mutate( Source = "EZACO")

df |>
  mutate( Classification = ifelse( Classification == "Felony" | Classification == "Misdemeanor", "Delinquency", Classification)) |>
  group_by(Classification, Year, County) |>
  summarize(count = sum(count)) |>
  filter(Classification != "Traffic Offense") -> df

df |> mutate( Source = "NE Justice") |> rbind(ezaco) -> df


ggplot(df, aes( x = Year, y = count, color = Classification)) +
  geom_point(aes(shape = Source)) +
  geom_line(aes(linetype = Source)) +
  facet_wrap(~ County) +
  theme_classic() +
  theme(legend.position = "top")
