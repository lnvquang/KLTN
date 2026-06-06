package com.dev.BETQ.dto.response;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewAnalysisResponse {
    private Long reviewId;
    private PersonalityResponse personality;
    private PersonalityResponse personality_logits;
    private MultitaskResponse multitask;
    private Integer cluster;
    private String cluster_label;
    private String preprocessed_text;

}