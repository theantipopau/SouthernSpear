// Copyright Southern Spear. All Rights Reserved.

#include "SSFirstPersonCameraMode.h"

#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"

USSFirstPersonCameraMode::USSFirstPersonCameraMode()
{
	FieldOfView = 90.f;
	ViewPitchMin = -85.f;
	ViewPitchMax = 85.f;
	BlendTime = 0.08f;
}

USSFirstPersonADSCameraMode::USSFirstPersonADSCameraMode()
{
	FieldOfView = 60.f;
	BlendTime = 0.15f;
}

void USSFirstPersonCameraMode::UpdateView(float DeltaTime)
{
	Super::UpdateView(DeltaTime); // pivot location/rotation, pitch clamp, FOV

	const ACharacter* Character = Cast<ACharacter>(GetTargetActor());
	const USkeletalMeshComponent* Mesh = Character ? Character->GetMesh() : nullptr;
	if (Mesh && Mesh->DoesSocketExist(EyeBone))
	{
		const FRotator Aim = View.ControlRotation;
		const FRotationMatrix Frame(FRotator(0.f, Aim.Yaw, 0.f));
		View.Location = Mesh->GetSocketLocation(EyeBone)
			+ Frame.GetUnitAxis(EAxis::X) * EyeOffset.X
			+ Frame.GetUnitAxis(EAxis::Y) * EyeOffset.Y
			+ FVector::UpVector * EyeOffset.Z;
	}
	View.Rotation = View.ControlRotation;
}
