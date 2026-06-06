package com.dev.BETQ.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class ReviewDetailResponse {

    private Long id;

    private String reviewText;

    private Double openness;
    private Double conscientiousness;
    private Double extraversion;
    private Double agreeableness;
    private Double neuroticism;

    private Double sentimentNegative;
    private Double sentimentNeutral;
    private Double sentimentPositive;

    private Double helpfulnessKeyAspects;
    private Double helpfulnessAdvice;
    private Double helpfulnessTotal;

    private Integer clusterId;
    private String clusterLabel;

    private Date createdAt;
}