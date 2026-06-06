package com.dev.BETQ.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;

@AllArgsConstructor
@NoArgsConstructor
@Data
@Builder
public class AdminReviewHistoryResponse {
    private Long id;
    private Long userId;
    private String fullName;
    private String reviewText;
    private Double sentimentPositive;
    private Integer clusterId;
    private String clusterLabel;
    private Date createdAt;
}
