package com.dev.BETQ.dto.response;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class HelpfulnessResponse {

    private Double key_aspects;
    private Double advice;
    private Double total;

}

