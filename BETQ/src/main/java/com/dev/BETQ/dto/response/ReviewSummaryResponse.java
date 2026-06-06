package com.dev.BETQ.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReviewSummaryResponse {
    private Long id;
    private String reviewText;
    private Double sentimentPositive;
    private Integer clusterId;
    private String clusterLabel;
    private Date createdAt;
}
