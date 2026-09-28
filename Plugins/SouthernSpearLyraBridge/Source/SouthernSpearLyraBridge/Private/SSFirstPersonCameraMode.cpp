// Copyright Southern Spear. All Rights Reserved.

#include "SSFirstPersonCameraMode.h"

#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "HAL/IConsoleManager.h"
#include "GameFramework/Character.h"
#include "SSCharacter.h"
#include "SSLocalHudState.h"
#include "SSUserPrefs.h"

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
	FovScale = 60.f / 90.f;
	bSightEye = true;
	BlendTime = 0.15f;
}

void USSFirstPersonCameraMode::UpdateView(float DeltaTime)
{
	FieldOfView = FSSUserPrefs::GetFieldOfView() * FovScale; // settings menu preference
	// Aiming through a magnified optic: the view narrows by its power (the HUD draws the eyepiece and reticle,
	// and the view model is hidden; producer: "scopes don't work at all").
	const UWorld* ViewWorld = GetTargetActor() ? GetTargetActor()->GetWorld() : nullptr;
	const USSLocalHudState* Hud = ViewWorld ? ViewWorld->GetSubsystem<USSLocalHudState>() : nullptr;
	if (bSightEye && Hud && Hud->OpticMagnification > 1.f)
	{
		const float Base = FMath::DegreesToRadians(FSSUserPrefs::GetFieldOfView());
		FieldOfView = FMath::RadiansToDegrees(2.f * FMath::Atan(FMath::Tan(Base * 0.5f) / Hud->OpticMagnification));
	}
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

	// Lean (ADR-024): the replicated lean slides the eye ~30 cm sideways, a little lower,
	// and rolls the view, eased so it reads as a body movement rather than a snap.
	if (const ASSCharacter* Soldier = Cast<ASSCharacter>(GetTargetActor()))
	{
		LeanAlpha = FMath::FInterpTo(LeanAlpha, static_cast<float>(Soldier->GetLean()), DeltaTime, 7.f);
		const FRotationMatrix Frame(View.Rotation);
		View.Location += Frame.GetUnitAxis(EAxis::Y) * (LeanAlpha * 30.f) + FVector::UpVector * (-6.f * FMath::Abs(LeanAlpha));
		View.Rotation.Roll += LeanAlpha * 10.f;
	}

	// Aiming with an optic: the eye sits behind the held weapon's Sight socket
	// (Tools/Unreal/add_sight_sockets.py) on the line of sight.
	static IConsoleVariable* BodyView = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.FP.BodyView"));
	if (bSightEye && Character && BodyView && BodyView->GetInt() != 0)
	{
		static const FName Sight(TEXT("Sight"));
		TArray<AActor*> Attached;
		Character->GetAttachedActors(Attached, true, true);
		for (const AActor* Actor : Attached)
		{
			TInlineComponentArray<UStaticMeshComponent*> Meshes(Actor);
			for (const UStaticMeshComponent* Weapon : Meshes)
			{
				if (Weapon->IsVisible() && Weapon->DoesSocketExist(Sight))
				{
					static IConsoleVariable* Relief = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.FP.EyeRelief"));
					const float EyeRelief = Relief ? Relief->GetFloat() : 20.f;
					View.Location = Weapon->GetSocketLocation(Sight) - View.Rotation.Vector() * EyeRelief;
					return;
				}
			}
		}
	}
}
