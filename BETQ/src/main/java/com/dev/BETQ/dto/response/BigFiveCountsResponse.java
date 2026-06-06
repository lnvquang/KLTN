package com.dev.BETQ.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class BigFiveCountsResponse {
    private Double openness;
    private Double conscientiousness;
    private Double extraversion;
    private Double agreeableness;
    private Double neuroticism;
}
