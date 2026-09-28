// Copyright Southern Spear. All Rights Reserved.

#include "SSClassSelectWidget.h"

#include "Animation/AnimSequence.h"
#include "Components/BackgroundBlur.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

namespace
{
	struct FRoleText
	{
		FText Name;
		FText Description;
		FText Standard; // kit on standard maps (matches Config/DefaultGame.ini Kits)
		FText Special;  // kit on Special Forces maps
		const TCHAR* StandardWeapon; // weapon id shown in the preview (the Kits' first item)
		const TCHAR* SpecialWeapon;
	};

	const FRoleText& RoleText(int32 Index)
	{
		static const FRoleText Roles[] = {
			{ NSLOCTEXT("SSClass", "Rifleman", "RIFLEMAN"),
			  NSLOCTEXT("SSClass", "RiflemanDesc", "The backbone of the section. Take and hold the ground."),
			  NSLOCTEXT("SSClass", "RiflemanStd", "A88 · SPECTER OPTIC  +  A9"), NSLOCTEXT("SSClass", "RiflemanSF", "A416 · TA31  +  A9"), TEXT("A88"), TEXT("A416") },
			{ NSLOCTEXT("SSClass", "Medic", "MEDIC"),
			  NSLOCTEXT("SSClass", "MedicDesc", "Keeps the section in the fight. Healing is not in the game yet."),
			  NSLOCTEXT("SSClass", "MedicStd", "A88 · SPECTER OPTIC  +  A9"), NSLOCTEXT("SSClass", "MedicSF", "A4 · TA31  +  A9"), TEXT("A88"), TEXT("A4") },
			{ NSLOCTEXT("SSClass", "MachineGunner", "MACHINE GUNNER"),
			  NSLOCTEXT("SSClass", "MachineGunnerDesc", "Suppresses from the flank so the section can move."),
			  NSLOCTEXT("SSClass", "MachineGunnerStd", "A89 LIGHT SUPPORT WEAPON  +  A9"), NSLOCTEXT("SSClass", "MachineGunnerSF", "A89 LIGHT SUPPORT WEAPON  +  A9"), TEXT("A89"), TEXT("A89") },
			{ NSLOCTEXT("SSClass", "Sniper", "SNIPER"),
			  NSLOCTEXT("SSClass", "SniperDesc", "Long-range precision from overwatch."),
			  NSLOCTEXT("SSClass", "SniperStd", "A25 · TA648 OPTIC  +  A9"), NSLOCTEXT("SSClass", "SniperSF", "A25 · TA648 OPTIC  +  A9"), TEXT("A25"), TEXT("A25") },
			{ NSLOCTEXT("SSClass", "Grenadier", "GRENADIER"),
			  NSLOCTEXT("SSClass", "GrenadierDesc", "Indirect fire for cover. Launcher fire is not in the game yet."),
			  NSLOCTEXT("SSClass", "GrenadierStd", "A88G · UNDERBARREL LAUNCHER  +  A9"), NSLOCTEXT("SSClass", "GrenadierSF", "A4 · TA31  +  A9"), TEXT("A88G"), TEXT("A4") },
		};
		return Roles[FMath::Clamp(Index, 0, 4)];
	}

	// Preview stage, 2.5 km above the map origin: nothing in the level reaches it, and the capture
	// renders only the stage (show-only list), so the background is plain.
	const FVector StageAt(0.f, 0.f, 250000.f);
	const TCHAR* InvisibleBody = TEXT("/Game/Characters/Heroes/Mannequin/Meshes/SKM_Manny_Invis.SKM_Manny_Invis");
	const TCHAR* IdlePose = TEXT("/Game/Characters/Heroes/Mannequin/Animations/Locomotion/Rifle/MM_Rifle_Idle_Hipfire.MM_Rifle_Idle_Hipfire");
	const TCHAR* SoldierClass = TEXT("/SSExp_ObjectiveAssault/Characters/B_SS_Soldier.B_SS_Soldier_C");

	UButton* ClassCard(UWidgetTree* T, int32 Index, const FRoleText& Role, UBorder*& OutEdge, UTextBlock*& OutWeapon)
	{
		UButton* Card = MenuButton(T, FText::GetEmpty(), 0.f);
		Card->ClearChildren();
		UHorizontalBox* Row = T->ConstructWidget<UHorizontalBox>();
		USizeBox* Size = T->ConstructWidget<USizeBox>();
		Size->SetWidthOverride(420.f);
		Size->SetHeightOverride(92.f);
		Size->AddChild(Row);
		Card->AddChild(Size);

		OutEdge = Plate(T, SSPalette::Brass500(), FMargin(0.f));
		USizeBox* EdgeSize = T->ConstructWidget<USizeBox>();
		EdgeSize->SetWidthOverride(3.f);
		EdgeSize->AddChild(OutEdge);
		AddH(Row, EdgeSize, false, VAlign_Fill);
		UTextBlock* Number = Text(T, 13, true, SSPalette::Brass300(), 200);
		Number->SetText(FText::FromString(FString::Printf(TEXT("0%d"), Index + 1)));
		AddH(Row, Number, false, VAlign_Top)->SetPadding(FMargin(14.f, 2.f, 14.f, 0.f));
		UVerticalBox* Body = T->ConstructWidget<UVerticalBox>();
		AddH(Row, Body, true, VAlign_Center);
		UTextBlock* Name = Text(T, 19, true, SSPalette::Sand100(), 100);
		Name->SetText(Role.Name);
		AddV(Body, Name);
		UTextBlock* Desc = Text(T, 11, false, SSPalette::Sage200());
		Desc->SetText(Role.Description);
		Desc->SetAutoWrapText(true);
		AddV(Body, Desc, 2.f);
		OutWeapon = Text(T, 10, true, SSPalette::Brass300(), 140);
		AddV(Body, OutWeapon, 5.f);
		return Card;
	}
}

bool USSClassSelectWidget::Initialize()
{
	if (!Super::Initialize())
	{
		return false;
	}
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return true;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	UBackgroundBlur* Blur = T->ConstructWidget<UBackgroundBlur>();
	Blur->SetBlurStrength(6.f);
	Fill(Root, Blur);
	Fill(Root, Plate(T, SSPalette::Ink950(0.72f), FMargin(0.f)));

	// Left: heading and the classes.
	UVerticalBox* Col = T->ConstructWidget<UVerticalBox>();
	Pin(Root, Col, FVector2D(0.f, 0.5f), FVector2D(72.f, 0.f));
	Kicker = Text(T, 12, true, SSPalette::Brass300(), 300);
	AddV(Col, Kicker);
	Heading = Text(T, 38, true, SSPalette::Sand100(), 120);
	AddV(Col, Heading, 2.f);
	AddV(Col, Rule(T, SSPalette::Brass500(), 2.f, 120.f), 10.f, HAlign_Left);

	const FName Handlers[] = {
		GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnRifleman),
		GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnMedic),
		GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnMachineGunner),
		GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnSniper),
		GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnGrenadier),
	};
	for (int32 Index = 0; Index < USSKitSelection::NumRoles; ++Index)
	{
		UBorder* Edge = nullptr;
		UTextBlock* Weapon = nullptr;
		UButton* Card = ClassCard(T, Index, RoleText(Index), Edge, Weapon);
		CardEdges.Add(Edge);
		WeaponTexts.Add(Weapon);
		FScriptDelegate Delegate;
		Delegate.BindUFunction(this, Handlers[Index]);
		Card->OnClicked.Add(Delegate);
		AddV(Col, Card, Index == 0 ? 22.f : 8.f, HAlign_Left);
		Cards.Add(Card);
	}
	UButton* Deploy = MenuButton(T, NSLOCTEXT("SSClass", "DeployButton", "DEPLOY"), 420.f, /*bPrimary=*/ true);
	FScriptDelegate DeployDelegate;
	DeployDelegate.BindUFunction(this, GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnDeploy));
	Deploy->OnClicked.Add(DeployDelegate);
	AddV(Col, Deploy, 22.f, HAlign_Left);
	UTextBlock* Hint = Text(T, 11, true, SSPalette::Sage400(), 200);
	Hint->SetText(NSLOCTEXT("SSClass", "Hint", "SELECT A CLASS, THEN DEPLOY  ·  CHANGE LATER WITH  L"));
	AddV(Col, Hint, 14.f);

	// Right: the selected soldier and weapon, as seen in game.
	UVerticalBox* Preview = T->ConstructWidget<UVerticalBox>();
	PreviewPanel = Preview;
	Pin(Root, Preview, FVector2D(1.f, 0.5f), FVector2D(-96.f, 0.f));
	UBorder* Frame = Plate(T, SSPalette::Line(0.9f), FMargin(1.f));
	AddV(Preview, Frame);
	USizeBox* ImageSize = T->ConstructWidget<USizeBox>();
	ImageSize->SetWidthOverride(540.f);
	ImageSize->SetHeightOverride(720.f);
	Frame->SetContent(ImageSize);
	PreviewImage = T->ConstructWidget<UImage>();
	ImageSize->AddChild(PreviewImage);
	PreviewName = Text(T, 30, true, SSPalette::Sand100(), 120);
	AddV(Preview, PreviewName, 14.f);
	PreviewWeapon = Text(T, 12, true, SSPalette::Brass300(), 200);
	AddV(Preview, PreviewWeapon, 2.f);
	return true;
}

void USSClassSelectWidget::Refresh()
{
	const USSKitSelection* Selection = GetWorld() ? GetWorld()->GetSubsystem<USSKitSelection>() : nullptr;
	const bool bSF = Selection && Selection->bSpecialForcesMap;
	for (int32 Index = 0; Index < WeaponTexts.Num(); ++Index)
	{
		WeaponTexts[Index]->SetText(bSF ? RoleText(Index).Special : RoleText(Index).Standard);
		const bool bOn = Index == Selected;
		CardEdges[Index]->SetBrushColor(bOn ? (bSF ? SSPalette::Sage200() : SSPalette::Brass500()) : SSPalette::Line(0.5f));
		Cards[Index]->SetRenderOpacity(bOn ? 1.f : 0.78f);
	}
	Kicker->SetText(bSF ? NSLOCTEXT("SSClass", "KickerSF", "SPECIAL FORCES  ·  CHOOSE YOUR ROLE")
		: NSLOCTEXT("SSClass", "KickerStd", "3 ACR  ·  CHOOSE YOUR ROLE"));
	PreviewName->SetText(RoleText(Selected).Name);
	PreviewWeapon->SetText(bSF ? RoleText(Selected).Special : RoleText(Selected).Standard);
}

void USSClassSelectWidget::Open(bool bAfterDeath)
{
	Heading->SetText(bAfterDeath ? NSLOCTEXT("SSClass", "Redeploy", "REDEPLOY") : NSLOCTEXT("SSClass", "Deploy", "SELECT CLASS"));
	ESSKitRole Current = ESSKitRole::Rifleman;
	const USSKitSelection* Selection = GetWorld() ? GetWorld()->GetSubsystem<USSKitSelection>() : nullptr;
	if (Selection && Selection->GetKit(GetOwningPlayer(), Current))
	{
		Selected = static_cast<int32>(Current);
	}
	Elapsed = 0.f;
	BuildStage();
	Select(Selected);
	SetVisibility(ESlateVisibility::Visible);
	if (APlayerController* Player = GetOwningPlayer())
	{
		FInputModeGameAndUI Input;
		Input.SetWidgetToFocus(TakeWidget());
		Player->SetInputMode(Input);
		Player->SetShowMouseCursor(true);
	}
}

void USSClassSelectWidget::Close()
{
	SetVisibility(ESlateVisibility::Collapsed);
	DestroyStage();
	if (APlayerController* Player = GetOwningPlayer())
	{
		Player->SetInputMode(FInputModeGameOnly());
		Player->SetShowMouseCursor(false);
	}
}

void USSClassSelectWidget::Select(int32 Index)
{
	Selected = FMath::Clamp(Index, 0, USSKitSelection::NumRoles - 1);
	Refresh();
	ShowWeapon(Selected);
}

void USSClassSelectWidget::OnDeploy()
{
	Pick(static_cast<ESSKitRole>(Selected));
}

void USSClassSelectWidget::Pick(ESSKitRole Role)
{
	if (USSKitSelection* Selection = GetWorld() ? GetWorld()->GetSubsystem<USSKitSelection>() : nullptr)
	{
		Selection->RequestKit(GetOwningPlayer(), Role);
	}
	Close();
}

void USSClassSelectWidget::OnRifleman()      { Select(0); }
void USSClassSelectWidget::OnMedic()         { Select(1); }
void USSClassSelectWidget::OnMachineGunner() { Select(2); }
void USSClassSelectWidget::OnSniper()        { Select(3); }
void USSClassSelectWidget::OnGrenadier()     { Select(4); }

void USSClassSelectWidget::BuildStage()
{
	UWorld* World = GetWorld();
	if (!World || Stage)
	{
		return;
	}
	FActorSpawnParameters Params;
	Params.ObjectFlags |= RF_Transient;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Stage = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform(StageAt), Params);
	if (!Stage)
	{
		return;
	}
	USceneComponent* Root = NewObject<USceneComponent>(Stage, TEXT("StageRoot"));
	Stage->SetRootComponent(Root);
	Root->RegisterComponent();
	Root->SetWorldLocation(StageAt);

	// Invisible animated body (Lyra's), with the friendly soldier parts following it, as in game.
	StageBody = NewObject<USkeletalMeshComponent>(Stage, TEXT("StageBody"));
	StageBody->SetupAttachment(Root);
	StageBody->SetSkeletalMesh(LoadObject<USkeletalMesh>(nullptr, InvisibleBody));
	StageBody->SetRelativeRotation(FRotator(0.f, -90.f, 0.f)); // the mannequin faces +Y; turn it to +X, the camera
	StageBody->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	StageBody->RegisterComponent();
	if (UAnimSequence* Idle = LoadObject<UAnimSequence>(nullptr, IdlePose))
	{
		StageBody->PlayAnimation(Idle, /*bLooping=*/ true);
	}
	// The parts live on the soldier Blueprint (SouthernSpearTeam, not a dependency of this module):
	// read its friendly part list by reflection.
	if (UClass* Soldier = LoadClass<AActor>(nullptr, SoldierClass))
	{
		const FArrayProperty* Parts = FindFProperty<FArrayProperty>(Soldier, TEXT("FriendlyParts"));
		const FObjectPropertyBase* Inner = Parts ? CastField<FObjectPropertyBase>(Parts->Inner) : nullptr;
		if (Inner)
		{
			FScriptArrayHelper Array(Parts, Parts->ContainerPtrToValuePtr<void>(Soldier->GetDefaultObject()));
			for (int32 Index = 0; Index < Array.Num(); ++Index)
			{
				if (USkeletalMesh* Mesh = Cast<USkeletalMesh>(Inner->GetObjectPropertyValue(Array.GetRawPtr(Index))))
				{
					USkeletalMeshComponent* Part = NewObject<USkeletalMeshComponent>(Stage);
					Part->SetupAttachment(StageBody);
					Part->SetSkeletalMesh(Mesh);
					Part->SetLeaderPoseComponent(StageBody);
					Part->RegisterComponent();
				}
			}
		}
	}

	// Backdrop wall and floor disc (engine shapes tinted to the UI palette): dark rifles need something
	// behind them to read against, and the soldier needs ground under the boots.
	UMaterialInterface* ShapeMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	auto Shape = [this, Root, ShapeMaterial](const TCHAR* Mesh, const FVector& At, const FRotator& Rotation, const FVector& Scale, const FLinearColor& Colour)
	{
		UStaticMeshComponent* Part = NewObject<UStaticMeshComponent>(Stage);
		Part->SetupAttachment(Root);
		Part->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, Mesh));
		Part->SetRelativeLocation(At);
		Part->SetRelativeRotation(Rotation);
		Part->SetRelativeScale3D(Scale);
		Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Part->SetCastShadow(false);
		if (UMaterialInstanceDynamic* Tint = ShapeMaterial ? UMaterialInstanceDynamic::Create(ShapeMaterial, Part) : nullptr)
		{
			Tint->SetVectorParameterValue(TEXT("Color"), Colour);
			Part->SetMaterial(0, Tint);
		}
		Part->RegisterComponent();
	};
	// The plane faces +Z; pitched -90 it faces the camera (+X), 2.6 m behind the soldier.
	Shape(TEXT("/Engine/BasicShapes/Plane.Plane"), FVector(-260.f, 0.f, 150.f), FRotator(-90.f, 0.f, 0.f), FVector(14.f, 14.f, 1.f), FLinearColor(0.16f, 0.17f, 0.13f));
	Shape(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"), FVector(0.f, 0.f, -1.f), FRotator::ZeroRotator, FVector(1.6f, 1.6f, 0.02f), FLinearColor(0.035f, 0.035f, 0.028f));

	// Studio lights: warm key front-left, cool fill right, rim behind. Only the stage is near them.
	auto Light = [this, Root](const FVector& At, float Intensity, const FLinearColor& Colour)
	{
		UPointLightComponent* Lamp = NewObject<UPointLightComponent>(Stage);
		Lamp->SetupAttachment(Root);
		Lamp->SetRelativeLocation(At);
		Lamp->SetIntensity(Intensity);
		Lamp->SetAttenuationRadius(1500.f);
		Lamp->SetLightColor(Colour);
		Lamp->SetCastShadows(false);
		Lamp->RegisterComponent();
	};
	Light(FVector(260.f, 160.f, 190.f), 9000.f, FLinearColor(1.f, 0.93f, 0.82f));
	Light(FVector(220.f, -200.f, 150.f), 7000.f, FLinearColor(0.8f, 0.88f, 1.f));
	Light(FVector(-220.f, 0.f, 220.f), 8000.f, FLinearColor(1.f, 0.85f, 0.65f));

	PreviewTarget = NewObject<UTextureRenderTarget2D>(this);
	PreviewTarget->InitAutoFormat(720, 960);
	PreviewTarget->ClearColor = SSPalette::Ink950();
	StageCamera = World->SpawnActor<ASceneCapture2D>(StageAt + FVector(330.f, 0.f, 96.f), FRotator(-1.f, 180.f, 0.f), Params);
	if (StageCamera)
	{
		USceneCaptureComponent2D* Capture = StageCamera->GetCaptureComponent2D();
		Capture->FOVAngle = 28.f;
		Capture->TextureTarget = PreviewTarget;
		Capture->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
		Capture->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
		Capture->ShowOnlyActors.Add(Stage);
		Capture->ShowFlags.SetFog(false);
		// Plain backdrop: the sky and clouds are not primitives, so the show-only list does not remove them.
		Capture->ShowFlags.SetAtmosphere(false);
		Capture->ShowFlags.SetCloud(false);
		Capture->ShowFlags.SetVolumetricFog(false);
		Capture->ShowFlags.SetMotionBlur(false);
		Capture->bCaptureEveryFrame = true;
	}
	PreviewImage->SetBrushResourceObject(PreviewTarget);
}

void USSClassSelectWidget::ShowWeapon(int32 Index)
{
	if (!Stage || !StageBody)
	{
		return;
	}
	USceneCaptureComponent2D* Capture = StageCamera ? StageCamera->GetCaptureComponent2D() : nullptr;
	if (StageWeapon)
	{
		if (Capture)
		{
			Capture->ShowOnlyActors.Remove(StageWeapon);
		}
		StageWeapon->Destroy();
		StageWeapon = nullptr;
	}
	const USSKitSelection* Selection = GetWorld() ? GetWorld()->GetSubsystem<USSKitSelection>() : nullptr;
	const TCHAR* Id = Selection && Selection->bSpecialForcesMap ? RoleText(Index).SpecialWeapon : RoleText(Index).StandardWeapon;
	const FString Path = FString::Printf(TEXT("/SSExp_ObjectiveAssault/Weapons/%s/B_SS_%s_Weapon.B_SS_%s_Weapon_C"), Id, Id, Id);
	UClass* WeaponClass = LoadClass<AActor>(nullptr, *Path);
	if (!WeaponClass)
	{
		return;
	}
	FActorSpawnParameters Params;
	Params.ObjectFlags |= RF_Transient;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	StageWeapon = GetWorld()->SpawnActor<AActor>(WeaponClass, FTransform(StageAt), Params);
	if (StageWeapon)
	{
		// Lyra's attachment for every A-series weapon: socket weapon_r, yaw -90 (WID_SS_* ActorsToSpawn).
		StageWeapon->AttachToComponent(StageBody, FAttachmentTransformRules::SnapToTargetNotIncludingScale, TEXT("weapon_r"));
		StageWeapon->SetActorRelativeRotation(FRotator(0.f, -90.f, 0.f));
		StageWeapon->SetActorEnableCollision(false);
		if (Capture)
		{
			Capture->ShowOnlyActors.Add(StageWeapon);
		}
	}
}

void USSClassSelectWidget::DestroyStage()
{
	for (AActor* Actor : TArray<AActor*>{ StageWeapon.Get(), StageCamera.Get(), Stage.Get() })
	{
		if (Actor)
		{
			Actor->Destroy();
		}
	}
	StageWeapon = nullptr;
	StageCamera = nullptr;
	Stage = nullptr;
	StageBody = nullptr;
}

void USSClassSelectWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Elapsed += InDeltaTime;
	for (int32 Index = 0; Index < Cards.Num(); ++Index)
	{
		Reveal(Cards[Index], Ease(Elapsed, 0.05f + 0.05f * Index, 0.35f), 24.f);
	}
	Reveal(PreviewPanel, Ease(Elapsed, 0.15f, 0.45f), -24.f);
	// Slow sway around the right-hand three-quarter view, where the rifle is carried. Only the soldier
	// turns (the weapon is attached to it); the backdrop and lights stay put, so no edge swings into view.
	if (StageBody)
	{
		StageBody->SetRelativeRotation(FRotator(0.f, -90.f - 55.f + 25.f * FMath::Sin(Elapsed * 0.45f), 0.f));
	}
}
