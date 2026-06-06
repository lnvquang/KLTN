package com.dev.BETQ.service;

import com.dev.BETQ.config.JwtProperties;
import com.dev.BETQ.dto.request.ReviewRequest;
import com.dev.BETQ.dto.response.*;
import com.dev.BETQ.entity.CustomerReview;
import com.dev.BETQ.entity.User;
import com.dev.BETQ.exception.AppException;
import com.dev.BETQ.exception.ErrorCode;
import com.dev.BETQ.repository.CustomerReviewRepository;
import com.dev.BETQ.repository.UserRepository;
import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jwt.SignedJWT;
import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Date;
import java.util.List;


@Service
public class ReviewService {
    @Autowired
    private CustomerReviewRepository repository;
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private RestTemplate restTemplate = new RestTemplate();
    @Autowired
    private JwtProperties jwtProperties;

    public ReviewAnalysisResponse analyzeReview(
            String token,
            ReviewRequest request
    ) throws Exception {

        if (token == null || token.isBlank()) {
            throw new AppException(ErrorCode.TOKEN_NOT_FOUND);
        }

        String jwt = token.substring(7);

        SignedJWT signedJWT = SignedJWT.parse(jwt);

        if (!signedJWT.verify(new MACVerifier(jwtProperties.getSecret()))) {
            throw new AppException(ErrorCode.TOKEN_INVALID);
        }

        Date expire = signedJWT.getJWTClaimsSet().getExpirationTime();

        if (expire.before(new Date())) {
            throw new AppException(ErrorCode.TOKEN_EXPIRED);
        }

        Long userId = Long.parseLong(
                signedJWT.getJWTClaimsSet().getSubject()
        );

        User user = userRepository.findById(userId)
                .orElseThrow(() ->
                        new AppException(ErrorCode.USER_NOT_FOUND));

        ReviewAiResponse aiResult =
                restTemplate.postForObject(
                        "http://127.0.0.1:8000/analyze-review",
                        request,
                        ReviewAiResponse.class
                );

        CustomerReview review = CustomerReview.builder()
                .reviewText(request.getText())

                .openness(
                        aiResult.getPersonality_logits().getOpenness()
                )
                .conscientiousness(
                        aiResult.getPersonality_logits().getConscientiousness()
                )
                .extraversion(
                        aiResult.getPersonality_logits().getExtraversion()
                )
                .agreeableness(
                        aiResult.getPersonality_logits().getAgreeableness()
                )
                .neuroticism(
                        aiResult.getPersonality_logits().getNeuroticism()
                )


                .sentimentNegative(
                        aiResult.getMultitask()
                                .getSentiment()
                                .getNegative()
                )
                .sentimentNeutral(
                        aiResult.getMultitask()
                                .getSentiment()
                                .getNeutral()
                )
                .sentimentPositive(
                        aiResult.getMultitask()
                                .getSentiment()
                                .getPositive()
                )


                .helpfulnessKeyAspects(
                        aiResult.getMultitask()
                                .getHelpfulness()
                                .getKey_aspects()
                )
                .helpfulnessAdvice(
                        aiResult.getMultitask()
                                .getHelpfulness()
                                .getAdvice()
                )
                .helpfulnessTotal(
                        aiResult.getMultitask()
                                .getHelpfulness()
                                .getTotal()
                )


                .clusterId(
                        aiResult.getCluster()
                )
                .clusterLabel(
                        aiResult.getCluster_label()
                )

                .createdAt(new Date())
                .user(user)
                .build();

        review = repository.save(review);

        return ReviewAnalysisResponse.builder()
                .reviewId(review.getId())
                .personality_logits(aiResult.getPersonality_logits())
                .personality(aiResult.getPersonality_probs())
                .multitask(aiResult.getMultitask())
                .cluster(aiResult.getCluster())
                .cluster_label(aiResult.getCluster_label())
                .preprocessed_text(aiResult.getPreprocessed_text())
                .build();
    }

    public List<ReviewHistoryResponse> getHistory(String token) throws Exception {


        if (token == null || token.isBlank()) {
            throw new AppException(ErrorCode.TOKEN_NOT_FOUND);
        }
        String jwt = token.substring(7);
        SignedJWT signedJWT = SignedJWT.parse(jwt);
        if (!signedJWT.verify(new MACVerifier(jwtProperties.getSecret()))) {
            throw new AppException(ErrorCode.TOKEN_INVALID);
        }
        Date expire = signedJWT.getJWTClaimsSet().getExpirationTime();
        if (expire.before(new Date())) {
            throw new AppException(ErrorCode.TOKEN_EXPIRED);
        }

        Long userId = Long.parseLong(signedJWT.getJWTClaimsSet().getSubject());
        return repository.findByUser_IdOrderByCreatedAtDesc(userId)
                .stream()
                .map(review -> ReviewHistoryResponse.builder()
                        .id(review.getId())
                        .reviewText(review.getReviewText())
                        .sentimentNegative(review.getSentimentNegative())
                        .sentimentPositive(review.getSentimentPositive())
                        .helpfulnessTotal(review.getHelpfulnessTotal())
                        .createdAt(review.getCreatedAt())
                        .build())
                .toList();
    }

    public ReviewDetailResponse getDetail(String token, Long reviewId) throws Exception {
        if (token == null || token.isBlank()) {
            throw new AppException(ErrorCode.TOKEN_NOT_FOUND);
        }
        String jwt = token.substring(7);
        SignedJWT signedJWT = SignedJWT.parse(jwt);
        if (!signedJWT.verify(new MACVerifier(jwtProperties.getSecret()))) {
            throw new AppException(ErrorCode.TOKEN_INVALID);
        }
        Date expire = signedJWT.getJWTClaimsSet().getExpirationTime();
        if (expire.before(new Date())) {
            throw new AppException(ErrorCode.TOKEN_EXPIRED);
        }

        Long userId = Long.parseLong(signedJWT.getJWTClaimsSet().getSubject());
        CustomerReview review =
                repository.findByIdAndUser_Id(
                                reviewId,
                                userId
                        )
                        .orElseThrow(() ->
                                new AppException(ErrorCode.REVIEW_NOTFOUND)
                        );

        return ReviewDetailResponse.builder()
                .id(review.getId())
                .reviewText(review.getReviewText())

                .openness(review.getOpenness())
                .conscientiousness(review.getConscientiousness())
                .extraversion(review.getExtraversion())
                .agreeableness(review.getAgreeableness())
                .neuroticism(review.getNeuroticism())

                .sentimentNegative(review.getSentimentNegative())
                .sentimentNeutral(review.getSentimentNeutral())
                .sentimentPositive(review.getSentimentPositive())

                .helpfulnessKeyAspects(review.getHelpfulnessKeyAspects())
                .helpfulnessAdvice(review.getHelpfulnessAdvice())
                .helpfulnessTotal(review.getHelpfulnessTotal())

                .createdAt(review.getCreatedAt())
                .build();
    }

}
