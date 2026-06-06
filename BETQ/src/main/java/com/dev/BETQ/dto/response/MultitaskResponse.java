package com.dev.BETQ.dto.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class MultitaskResponse {
    private SentimentResponse sentiment;
    private HelpfulnessResponse helpfulness;

}