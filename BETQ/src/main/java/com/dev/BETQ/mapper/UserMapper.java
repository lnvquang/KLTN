package com.dev.BETQ.mapper;
import com.dev.BETQ.dto.response.UserResponse;
import com.dev.BETQ.entity.User;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface UserMapper {


    UserResponse toDto(User user);

}

