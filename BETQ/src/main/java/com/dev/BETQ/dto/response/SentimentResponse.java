package com.dev.BETQ.dto.response;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SentimentResponse {
    private Double negative;
    private Double neutral;
    private Double positive;

}