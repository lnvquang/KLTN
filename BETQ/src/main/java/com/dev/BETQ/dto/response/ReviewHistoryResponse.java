package com.dev.BETQ.dto.response;
import lombok.Builder;
import lombok.Data;

import java.util.Date;

@Data
@Builder
public class ReviewHistoryResponse {

    private Long id;
    private String reviewText;

    private Double sentimentPositive;
    private Double sentimentNegative;
    private Double helpfulnessTotal;

    private Date createdAt;
}