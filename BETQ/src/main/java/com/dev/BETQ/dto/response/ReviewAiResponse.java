package com.dev.BETQ.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@Builder
@AllArgsConstructor
public class ReviewAiResponse {
    private PersonalityResponse personality_logits;
    private PersonalityResponse personality_probs;
    private MultitaskResponse multitask;
    private Integer cluster;
    private String cluster_label;
    private String preprocessed_text;
    private Boolean cluster_model_ready;
    private String message;
}