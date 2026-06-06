package com.dev.BETQ.exception;

import com.dev.BETQ.dto.response.ApiResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalException {
    @ExceptionHandler(value = AppException.class)
    ResponseEntity<ApiResponse<?>> handleAppException(AppException exception) {
        ErrorCode code = exception.getCode();
        ApiResponse<?> response = ApiResponse.builder()
                .status(code.getStatus())
                .code(code.getCode())
                .message(code.getMessage())
                .build();
        return ResponseEntity
                .status(code.getStatus())
                .body(response);

    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ApiResponse<?>> handleValidException(MethodArgumentNotValidException exception) {

        Map<String, String> errors = new HashMap<>();

        exception.getBindingResult().getFieldErrors()
                .forEach(error -> errors.put(error.getField(), error.getDefaultMessage()));

        ApiResponse<?> response = ApiResponse.builder()
                .status(400)
                .code("VALIDATION_ERROR")
                .message("Validation failed")
                .result(errors)
                .build();

        return ResponseEntity.badRequest().body(response);
    }

}
