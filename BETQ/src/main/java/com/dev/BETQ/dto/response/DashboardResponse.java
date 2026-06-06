package com.dev.BETQ.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class DashboardResponse {

    private Long totalUsers;

    private Long totalReviews;

    private Long positiveReviews;

    private Long neutralReviews;

    private Long negativeReviews;
}
